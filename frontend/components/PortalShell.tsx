"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getRole, logout } from "@/lib/api";
import type { Role } from "@/types/api";

type NavItem = { href: string; label: string };

const navByRole: Record<Role, NavItem[]> = {
  engineer: [
    { href: "/engineer/dashboard", label: "Dashboard" },
    { href: "/engineer/profile", label: "My Profile" },
    { href: "/engineer/passport", label: "Capability Passport" },
    { href: "/engineer/resume", label: "Resume Intelligence" },
    { href: "/engineer/opportunities", label: "Opportunities" },
    { href: "/engineer/applications", label: "My Applications" },
    { href: "/engineer/assessments", label: "Assessments" },
    { href: "/engineer/gaps", label: "Skill Gaps" },
    { href: "/engineer/learning-path", label: "Learning Path" },
  ],
  admin: [
    { href: "/admin/dashboard", label: "Dashboard" },
    { href: "/admin/jds", label: "Job Descriptions" },
    { href: "/admin/applications", label: "Applications" },
    { href: "/admin/assessments", label: "Assessments" },
    { href: "/admin/engineers", label: "Engineers" },
    { href: "/admin/teams", label: "Teams" },
  ],
  leadership: [
    { href: "/leadership/dashboard", label: "Dashboard" },
    { href: "/leadership/capabilities", label: "Capabilities" },
    { href: "/leadership/demand", label: "Demand & Supply" },
    { href: "/leadership/analytics", label: "Analytics" },
    { href: "/leadership/observability", label: "Observability" },
    { href: "/leadership/deployments", label: "Deployments" },
  ],
};

export default function PortalShell({ children, role }: { children: React.ReactNode; role: Role }) {
  const pathname = usePathname();
  const router = useRouter();
  const currentRole = getRole();
  const items = navByRole[role];

  function signOut() {
    logout();
    router.push("/login");
  }

  if (currentRole !== role && !(role === "leadership" && currentRole === "admin")) {
    return <main className="min-h-screen bg-[#0A0F1C] p-8 text-[#F0F4FF]">Access denied. Sign in with an authorized account.</main>;
  }

  return (
    <div className="min-h-screen bg-[#0A0F1C] text-[#F0F4FF]">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-[#1E2D45] bg-[#0A0F1C] lg:block">
        <div className="border-b border-[#1E2D45] px-6 py-6">
          <Link href={role === "engineer" ? "/engineer/dashboard" : role === "admin" ? "/admin/dashboard" : "/leadership/dashboard"} className="block">
            <span className="text-xs font-medium uppercase tracking-[0.3em] text-[#00B5E2]">NEXUS V3</span>
            <span className="mt-2 block text-lg font-semibold tracking-tight text-[#F0F4FF]">Capability Intelligence</span>
          </Link>
        </div>
        <nav className="space-y-1 p-4">
          {items.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return <Link key={item.href} href={item.href} className={`block border-l-2 px-4 py-3 text-sm transition ${active ? "border-[#00B5E2] bg-[#00B5E2]/10 text-[#00B5E2]" : "border-transparent text-[#8899BB] hover:bg-[#1A2235] hover:text-[#F0F4FF]"}`}>{item.label}</Link>;
          })}
        </nav>
        <div className="absolute bottom-0 left-0 right-0 border-t border-[#1E2D45] p-4">
          <p className="mb-3 truncate text-xs text-[#8899BB]">{currentRole ?? role} workspace</p>
          <button onClick={signOut} className="w-full rounded-lg border border-[#1E2D45] px-3 py-2 text-left text-sm text-[#8899BB] hover:border-[#00B5E2] hover:text-[#F0F4FF]">Sign out</button>
        </div>
      </aside>
      <div className="min-h-screen lg:ml-64">
        <div className="border-b border-[#1E2D45] bg-[#0A0F1C]/90 px-6 py-4 lg:hidden">
          <div className="flex items-center justify-between"><Link href="/" className="font-semibold text-[#F0F4FF]">NEXUS V3</Link><button onClick={signOut} className="text-sm text-[#8899BB]">Sign out</button></div>
          <nav className="mt-4 flex gap-2 overflow-x-auto">{items.map((item) => <Link key={item.href} href={item.href} className="whitespace-nowrap rounded-lg border border-[#1E2D45] px-3 py-2 text-xs text-[#8899BB]">{item.label}</Link>)}</nav>
        </div>
        <main className="min-h-screen p-5 sm:p-8">{children}</main>
      </div>
    </div>
  );
}
