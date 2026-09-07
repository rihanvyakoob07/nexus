type Message = {
  role: "assistant" | "user";
  text: string;
};

type ArenaChatProps = {
  messages: Message[];
};

export default function ArenaChat({ messages }: ArenaChatProps) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Assessment flow</h3>
        <span className="text-xs uppercase tracking-[0.2em] text-sky-300">Arena</span>
      </div>
      <div className="space-y-3">
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
              message.role === "assistant"
                ? "bg-sky-500/15 text-sky-100"
                : "ml-auto bg-emerald-500/15 text-emerald-100"
            }`}
          >
            {message.text}
          </div>
        ))}
      </div>
    </div>
  );
}
