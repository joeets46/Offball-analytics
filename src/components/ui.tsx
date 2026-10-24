import type { ButtonHTMLAttributes, HTMLAttributes, InputHTMLAttributes, ReactNode } from 'react'
import { cn } from '../lib/utils'

export function Button({ className, variant = 'primary', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'outline' | 'ghost' | 'danger' }) {
  return <button className={cn('inline-flex items-center justify-center gap-2 rounded-lg px-3.5 py-2.5 text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-orange-300 disabled:cursor-not-allowed disabled:opacity-50', variant === 'primary' && 'bg-orange-500 text-white hover:bg-orange-600', variant === 'outline' && 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800', variant === 'ghost' && 'text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-white', variant === 'danger' && 'bg-red-50 text-red-600 hover:bg-red-100', className)} {...props} />
}

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900', className)} {...props} />
}

export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'success' | 'warning' | 'orange' | 'purple' }) {
  return <span className={cn('inline-flex rounded-full px-2 py-1 text-[11px] font-semibold', tone === 'success' && 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300', tone === 'warning' && 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300', tone === 'orange' && 'bg-orange-50 text-orange-700 dark:bg-orange-950/50 dark:text-orange-300', tone === 'purple' && 'bg-violet-50 text-violet-700 dark:bg-violet-950/50 dark:text-violet-300', tone === 'neutral' && 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300')}>{children}</span>
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-orange-400 focus:ring-2 focus:ring-orange-100 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:ring-orange-950" {...props} />
}
