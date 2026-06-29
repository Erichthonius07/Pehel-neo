import ChatPageClient from "./ChatPageClient";

export function generateStaticParams() {
  return [{ id: 'demo' }];
}

export default function ChatPage({ params }: { params: { id: string } }) {
  return <ChatPageClient id={params.id} />;
}