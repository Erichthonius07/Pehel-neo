import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap text-xs font-semibold uppercase tracking-wider focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-text-primary text-white hover:bg-[#333333]",
        outline: "border border-text-primary bg-transparent text-text-primary hover:bg-text-primary hover:text-white",
        ghost: "bg-transparent text-text-muted hover:text-text-primary",
        danger: "bg-priority-high text-white hover:bg-[#A31818]",
      },
      size: {
        default: "h-12 px-6 py-3",
        sm: "h-8 px-3 py-1",
        lg: "h-14 px-8 py-4",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
)

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({ className, variant, size, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"
  return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
})
Button.displayName = "Button"

export { Button, buttonVariants }