import { useRef } from "react";

const PaperclipIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
  </svg>
);

const SendIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" />
    <polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
);

interface ChatInputProps {
  value: string;
  onChange: (val: string) => void;
  onSend: () => void;
  onUploadClick: () => void;
  disabled?: boolean;
}

export default function ChatInput({ value, onChange, onSend, onUploadClick, disabled }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
      if (textareaRef.current) textareaRef.current.style.height = "auto";
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm flex flex-col gap-2 px-4 py-3">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="Ketik pesanmu di sini..."
        rows={1}
        disabled={disabled}
        className="w-full resize-none text-sm text-gray-700 placeholder-gray-300 outline-none bg-transparent leading-relaxed disabled:opacity-50"
        style={{ minHeight: 28 }}
      />
      <div className="flex items-center justify-between">
        <button
          onClick={onUploadClick}
          className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600 border border-gray-200 rounded-lg px-3 py-1.5 transition-colors"
        >
          <PaperclipIcon />
          Upload KHS
        </button>
        <button
          onClick={onSend}
          disabled={!value.trim() || disabled}
          className="w-9 h-9 rounded-full flex items-center justify-center text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          style={{ backgroundColor: "#307045" }}
        >
          <SendIcon />
        </button>
      </div>
    </div>
  );
}   