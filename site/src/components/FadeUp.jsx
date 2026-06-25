import { useInView } from '../hooks/useInView'

export default function FadeUp({ children, delay = 0, className = '' }) {
  const ref = useInView()
  return (
    <div ref={ref} className={`fade-up ${className}`} style={delay ? { transitionDelay: `${delay}ms` } : undefined}>
      {children}
    </div>
  )
}
