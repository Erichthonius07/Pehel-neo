import IssueDetailClient from "./IssueDetailClient";

export function generateStaticParams() {
  return [{ id: 'demo' }];
}

export default function IssuePage({ params }: { params: { id: string } }) {
  return <IssueDetailClient id={params.id} />;
}