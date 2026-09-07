import PortalShell from "@/components/PortalShell";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <PortalShell role="admin">{children}</PortalShell>;
}
