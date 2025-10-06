"""
MatchingService - Handles fuzzy matching of transactions to receipts.

This module implements the matching algorithm that links transactions
to receipts based on amount, date, and merchant similarity.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from ..models.transaction import Transaction
from ..models.receipt import Receipt
from ..repositories.match_result_repository import MatchResultRepository
from ..repositories.receipt_repository import ReceiptRepository
from ..repositories.session_repository import SessionRepository
from ..repositories.transaction_repository import TransactionRepository


class MatchingService:
    """
    Service for matching transactions to receipts using fuzzy logic.

    Implements multi-factor matching algorithm:
    - Amount matching (exact or within threshold)
    - Date proximity (within N days)
    - Merchant/vendor name similarity (Levenshtein distance)
    """

    # Matching thresholds
    AMOUNT_TOLERANCE = Decimal("0.01")  # ±$0.01
    DATE_WINDOW_DAYS = 3  # ±3 days
    MERCHANT_SIMILARITY_THRESHOLD = 0.8  # 80% similarity
    CONFIDENCE_THRESHOLD = 0.7  # 70% confidence for auto-match

    # Weights for confidence calculation
    WEIGHT_AMOUNT = 0.5
    WEIGHT_DATE = 0.3
    WEIGHT_MERCHANT = 0.2

    def __init__(
        self,
        session_repo: SessionRepository,
        transaction_repo: TransactionRepository,
        receipt_repo: ReceiptRepository,
        match_result_repo: MatchResultRepository
    ):
        """
        Initialize matching service.

        Args:
            session_repo: SessionRepository instance
            transaction_repo: TransactionRepository instance
            receipt_repo: ReceiptRepository instance
            match_result_repo: MatchResultRepository instance
        """
        self.session_repo = session_repo
        self.transaction_repo = transaction_repo
        self.receipt_repo = receipt_repo
        self.match_result_repo = match_result_repo

    async def match_transactions_to_receipts(self, session_id: UUID) -> None:
        """
        Match all transactions to receipts for a session.

        Args:
            session_id: UUID of the session

        Note:
            This is the main matching workflow:
            1. Get all transactions and receipts for session
            2. For each transaction, find best matching receipt
            3. Create MatchResult for each transaction
            4. Update session counts and status
        """
        try:
            # Get all transactions and receipts
            transactions = await self.transaction_repo.get_transactions_by_session(
                session_id
            )
            receipts = await self.receipt_repo.get_receipts_by_session(session_id)

            # Track used receipts (one receipt can only match one transaction)
            used_receipt_ids = set()

            # Create match results
            match_results = []

            for transaction in transactions:
                # Find best matching receipt
                best_match, confidence, factors = self._find_best_match(
                    transaction, receipts, used_receipt_ids
                )

                if best_match and confidence >= self.CONFIDENCE_THRESHOLD:
                    # High confidence match
                    match_status = "matched"
                    used_receipt_ids.add(best_match.id)
                    receipt_id = best_match.id
                    match_reason = f"Matched with {confidence:.2%} confidence"
                elif best_match:
                    # Low confidence - needs manual review
                    match_status = "manual_review"
                    receipt_id = best_match.id
                    match_reason = f"Low confidence match ({confidence:.2%}) - needs review"
                else:
                    # No match found
                    match_status = "unmatched"
                    receipt_id = None
                    match_reason = "No matching receipt found"

                # Calculate differences if we have a match
                amount_diff = None
                date_diff = None
                merchant_sim = None

                if best_match:
                    amount_diff = abs(transaction.amount - best_match.amount)
                    date_diff = abs((transaction.transaction_date - best_match.receipt_date).days)
                    merchant_sim = factors.get("merchant_match", 0.0)

                match_data = {
                    "confidence_score": Decimal(str(confidence)),
                    "match_status": match_status,
                    "match_reason": match_reason,
                    "amount_difference": amount_diff,
                    "date_difference_days": date_diff,
                    "merchant_similarity": Decimal(str(merchant_sim)) if merchant_sim is not None else None,
                    "matching_factors": factors
                }

                match_results.append({
                    "session_id": session_id,
                    "transaction_id": transaction.id,
                    "receipt_id": receipt_id,
                    **match_data
                })

            # Bulk create match results
            if match_results:
                await self.match_result_repo.bulk_create_match_results(match_results)

            # Update session counts
            await self.session_repo.update_session_counts(session_id)

            # Update session status to completed
            await self.session_repo.update_session_status(session_id, "completed")

        except Exception as e:
            # Update session status to failed
            await self.session_repo.update_session_status(session_id, "failed")
            raise

    def _find_best_match(
        self,
        transaction: Transaction,
        receipts: List[Receipt],
        used_receipt_ids: set
    ) -> Tuple[Optional[Receipt], float, Dict]:
        """
        Find the best matching receipt for a transaction.

        Args:
            transaction: Transaction to match
            receipts: List of available receipts
            used_receipt_ids: Set of receipt IDs already matched

        Returns:
            Tuple of (best matching receipt, confidence score, matching factors dict)
        """
        best_receipt = None
        best_confidence = 0.0
        best_factors = {}

        for receipt in receipts:
            # Skip if receipt already used
            if receipt.id in used_receipt_ids:
                continue

            # Calculate match factors
            amount_score = self._calculate_amount_match(
                transaction.amount, receipt.amount
            )
            date_score = self._calculate_date_proximity(
                transaction.transaction_date, receipt.receipt_date
            )
            merchant_score = self._calculate_merchant_similarity(
                transaction.merchant_name, receipt.vendor_name
            )

            # Calculate weighted confidence score
            confidence = (
                amount_score * self.WEIGHT_AMOUNT +
                date_score * self.WEIGHT_DATE +
                merchant_score * self.WEIGHT_MERCHANT
            )

            factors = {
                "amount_match": amount_score,
                "date_proximity": date_score,
                "merchant_match": merchant_score,
                "algorithm_version": "v1.0.0",
                "weights": {
                    "amount": self.WEIGHT_AMOUNT,
                    "date": self.WEIGHT_DATE,
                    "merchant": self.WEIGHT_MERCHANT
                }
            }

            # Update best match if this is better
            if confidence > best_confidence:
                best_confidence = confidence
                best_receipt = receipt
                best_factors = factors

        return best_receipt, best_confidence, best_factors

    def _calculate_amount_match(
        self, trans_amount: Decimal, receipt_amount: Decimal
    ) -> float:
        """
        Calculate amount match score (0.0-1.0).

        Args:
            trans_amount: Transaction amount
            receipt_amount: Receipt amount

        Returns:
            Score from 0.0 (no match) to 1.0 (exact match)
        """
        diff = abs(trans_amount - receipt_amount)

        if diff == 0:
            return 1.0
        elif diff <= self.AMOUNT_TOLERANCE:
            # Linear decay within tolerance
            return 1.0 - float(diff / self.AMOUNT_TOLERANCE) * 0.1
        else:
            # Exponential decay beyond tolerance
            # At 10% difference, score is ~0.37
            # At 20% difference, score is ~0.14
            avg_amount = (trans_amount + receipt_amount) / 2
            if avg_amount == 0:
                return 0.0
            percent_diff = float(diff / avg_amount)
            return max(0.0, 1.0 / (1.0 + percent_diff * 10))

    def _calculate_date_proximity(
        self, trans_date: date, receipt_date: date
    ) -> float:
        """
        Calculate date proximity score (0.0-1.0).

        Args:
            trans_date: Transaction date
            receipt_date: Receipt date

        Returns:
            Score from 0.0 (far apart) to 1.0 (same date)
        """
        day_diff = abs((trans_date - receipt_date).days)

        if day_diff == 0:
            return 1.0
        elif day_diff <= self.DATE_WINDOW_DAYS:
            # Linear decay within window
            return 1.0 - (day_diff / self.DATE_WINDOW_DAYS) * 0.3
        else:
            # Exponential decay beyond window
            return max(0.0, 0.7 / (1.0 + (day_diff - self.DATE_WINDOW_DAYS) * 0.5))

    def _calculate_merchant_similarity(
        self, merchant_name: str, vendor_name: str
    ) -> float:
        """
        Calculate merchant name similarity using Levenshtein distance.

        Args:
            merchant_name: Merchant name from transaction
            vendor_name: Vendor name from receipt

        Returns:
            Similarity score from 0.0 (no match) to 1.0 (exact match)
        """
        # Normalize strings
        merchant = merchant_name.lower().strip()
        vendor = vendor_name.lower().strip()

        # Exact match
        if merchant == vendor:
            return 1.0

        # Contains match
        if merchant in vendor or vendor in merchant:
            return 0.9

        # Levenshtein distance
        distance = self._levenshtein_distance(merchant, vendor)
        max_len = max(len(merchant), len(vendor))

        if max_len == 0:
            return 0.0

        similarity = 1.0 - (distance / max_len)
        return max(0.0, similarity)

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein distance between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Edit distance (number of single-character edits required)
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]
