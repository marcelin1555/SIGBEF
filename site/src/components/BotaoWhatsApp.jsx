import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faWhatsapp } from '@fortawesome/free-brands-svg-icons'

export default function BotaoWhatsApp() {
  return (
    <a
      href="https://w.app/sigbef"
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Fale conosco no WhatsApp"
      title="Fale conosco no WhatsApp"
      className="fixed bottom-5 right-5 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-[#25D366] text-white shadow-xl transition-transform hover:scale-110 hover:bg-[#1EBE5D]"
    >
      <FontAwesomeIcon icon={faWhatsapp} className="text-3xl" />
    </a>
  )
}
