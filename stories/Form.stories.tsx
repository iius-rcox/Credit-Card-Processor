import type { Meta, StoryObj } from '@storybook/react'
import { useForm } from 'react-hook-form'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useState } from 'react'

const meta: Meta<typeof Form> = {
  title: 'Components/Form',
  component: Form,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof meta>

// Form data types
interface BasicFormData {
  email: string
  password: string
}

interface AdvancedFormData {
  firstName: string
  lastName: string
  email: string
  phone?: string
  message: string
}

export const BasicForm: Story = {
  render: () => {
    const form = useForm<BasicFormData>({
      defaultValues: {
        email: '',
        password: '',
      },
    })

    const onSubmit = (data: BasicFormData) => {
      console.log('Form submitted:', data)
      alert('Form submitted successfully!')
    }

    return (
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 max-w-md">
          <FormField
            control={form.control}
            name="email"
            rules={{
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address',
              },
            }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input placeholder="Enter your email" {...field} />
                </FormControl>
                <FormDescription>
                  We'll never share your email with anyone else.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="password"
            rules={{
              required: 'Password is required',
              minLength: {
                value: 8,
                message: 'Password must be at least 8 characters',
              },
            }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Password</FormLabel>
                <FormControl>
                  <Input type="password" placeholder="Enter your password" {...field} />
                </FormControl>
                <FormDescription>
                  Choose a strong password with at least 8 characters.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full">
            Sign In
          </Button>
        </form>
      </Form>
    )
  },
}

export const FormWithValidation: Story = {
  render: () => {
    const [isSubmitted, setIsSubmitted] = useState(false)
    const form = useForm<AdvancedFormData>({
      defaultValues: {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        message: '',
      },
    })

    const onSubmit = (data: AdvancedFormData) => {
      console.log('Advanced form submitted:', data)
      setIsSubmitted(true)
      setTimeout(() => setIsSubmitted(false), 3000)
    }

    return (
      <div className="space-y-4 max-w-md">
        {isSubmitted && (
          <Alert>
            <AlertDescription>
              Form submitted successfully! Check the console for form data.
            </AlertDescription>
          </Alert>
        )}

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="firstName"
                rules={{
                  required: 'First name is required',
                  minLength: {
                    value: 2,
                    message: 'First name must be at least 2 characters',
                  },
                }}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>First Name</FormLabel>
                    <FormControl>
                      <Input placeholder="John" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="lastName"
                rules={{
                  required: 'Last name is required',
                  minLength: {
                    value: 2,
                    message: 'Last name must be at least 2 characters',
                  },
                }}
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Last Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Doe" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="email"
              rules={{
                required: 'Email is required',
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: 'Invalid email address',
                },
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email Address</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="john.doe@example.com" {...field} />
                  </FormControl>
                  <FormDescription>
                    We'll use this email to contact you.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="phone"
              rules={{
                pattern: {
                  value: /^[\+]?[1-9][\d]{0,15}$/,
                  message: 'Invalid phone number',
                },
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Phone Number (Optional)</FormLabel>
                  <FormControl>
                    <Input type="tel" placeholder="+1 (555) 123-4567" {...field} />
                  </FormControl>
                  <FormDescription>
                    Include country code if outside the US.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="message"
              rules={{
                required: 'Message is required',
                minLength: {
                  value: 10,
                  message: 'Message must be at least 10 characters',
                },
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Message</FormLabel>
                  <FormControl>
                    <textarea
                      className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      placeholder="Tell us about your project..."
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Provide details about your inquiry or project.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button
              type="submit"
              className="w-full"
              disabled={form.formState.isSubmitting}
            >
              {form.formState.isSubmitting ? 'Submitting...' : 'Submit Form'}
            </Button>
          </form>
        </Form>
      </div>
    )
  },
}

export const FormWithErrors: Story = {
  render: () => {
    const form = useForm<BasicFormData>({
      defaultValues: {
        email: 'invalid-email',
        password: '123',
      },
    })

    // Trigger validation to show errors
    form.trigger()

    const onSubmit = (data: BasicFormData) => {
      console.log('Form submitted:', data)
    }

    return (
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6 max-w-md">
          <FormField
            control={form.control}
            name="email"
            rules={{
              required: 'Email is required',
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: 'Invalid email address',
              },
            }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input placeholder="Enter your email" {...field} />
                </FormControl>
                <FormDescription>
                  This field shows a validation error.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="password"
            rules={{
              required: 'Password is required',
              minLength: {
                value: 8,
                message: 'Password must be at least 8 characters',
              },
            }}
            render={({ field }) => (
              <FormItem>
                <FormLabel>Password</FormLabel>
                <FormControl>
                  <Input type="password" placeholder="Enter your password" {...field} />
                </FormControl>
                <FormDescription>
                  This field also shows a validation error.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full">
            Submit (Will show errors)
          </Button>
        </form>
      </Form>
    )
  },
}

export const BlueThemeShowcase: Story = {
  render: () => {
    const form = useForm<{ testField: string }>({
      defaultValues: { testField: '' },
    })

    return (
      <div className="space-y-6">
        <h3 className="text-lg font-semibold">Blue Theme Form Elements</h3>

        <Form {...form}>
          <form className="space-y-6 max-w-md">
            <FormField
              control={form.control}
              name="testField"
              render={({ field }) => (
                <FormItem>
                  <FormLabel className="text-primary">
                    Blue Theme Label
                  </FormLabel>
                  <FormControl>
                    <Input
                      placeholder="Focus to see blue ring"
                      className="focus-visible:ring-primary"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription className="text-muted-foreground">
                    Description text uses muted foreground color.
                  </FormDescription>
                  <FormMessage className="text-destructive">
                    Error messages use destructive color (red).
                  </FormMessage>
                </FormItem>
              )}
            />

            <div className="space-y-2">
              <Button variant="default" type="button" className="mr-2">
                Primary Blue Button
              </Button>
              <Button variant="outline" type="button" className="mr-2">
                Blue Outline Button
              </Button>
              <Button variant="secondary" type="button">
                Secondary Button
              </Button>
            </div>
          </form>
        </Form>
      </div>
    )
  },
}

export const ResponsiveForm: Story = {
  render: () => {
    const form = useForm<AdvancedFormData>({
      defaultValues: {
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        message: '',
      },
    })

    const onSubmit = (data: AdvancedFormData) => {
      console.log('Responsive form submitted:', data)
    }

    return (
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <h3 className="text-lg font-semibold mb-4">Responsive Form Layout</h3>

          {/* Single column on mobile, two columns on larger screens */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="firstName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>First Name</FormLabel>
                  <FormControl>
                    <Input placeholder="First name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="lastName"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Last Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Last name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          {/* Full width fields */}
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input type="email" placeholder="Email address" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Phone</FormLabel>
                <FormControl>
                  <Input type="tel" placeholder="Phone number" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <Button type="submit" className="w-full md:w-auto">
            Submit Responsive Form
          </Button>
        </form>
      </Form>
    )
  },
}