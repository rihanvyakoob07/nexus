"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getRole, logout } from "@/lib/api";
import type { Role } from "@/types/api";

type NavItem = { href: string; label: string };

const navByRole: Record<Role, NavItem[]> = {
  engineer: [
    { href: "/engineer/dashboard", label: "Overview" },
    { href: "/engineer/passport", label: "Capability Passport" },
    { href: "/engineer/opportunities", label: "Opportunities" },
    { href: "/engineer/assessments", label: "Assessments" },
    { href: "/engineer/gaps", label: "Skill Gaps" },
    { href: "/engineer/learning-path", label: "Learning Path" },
    { href: "/engineer/applications", label: "Applications" },
    { href: "/engineer/profile", label: "Profile" },
  ],
  admin: [
    { href: "/admin/dashboard", label: "Overview" },
    { href: "/admin/jds", label: "Job Descriptions" },
    { href: "/admin/engineers", label: "Engineering Pool" },
    { href: "/admin/applications", label: "Applications" },
    { href: "/admin/assessments", label: "Assessments" },
    { href: "/admin/teams", label: "Teams" },
  ],
  leadership: [
    { href: "/leadership/dashboard", label: "Overview" },
    { href: "/leadership/capabilities", label: "Capabilities" },
    { href: "/leadership/demand", label: "Demand & Supply" },
    { href: "/leadership/analytics", label: "Analytics" },
    { href: "/leadership/deployments", label: "Deployments" },
    { href: "/leadership/observability", label: "AI Operations" },
  ],
};

const homeByRole: Record<Role, string> = {
  engineer: "/engineer/dashboard",
  admin: "/admin/dashboard",
  leadership: "/leadership/dashboard",
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
    return <main className="flex min-h-screen items-center justify-center bg-[#F7F8FB] p-8 text-[#172033]"><div className="hcl-card max-w-md p-8 text-center"><p className="text-sm font-semibold text-[#B42318]">Access denied</p><p className="mt-2 text-sm text-[#64748B]">Your account is not authorized for this workspace.</p><Link className="mt-5 inline-block text-sm font-semibold text-[#0F5FDC]" href="/login">Return to sign in</Link></div></main>;
  }

  return (
    <div className="min-h-screen bg-[#F7F8FB] text-[#172033]">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-[#DFE4EC] bg-white lg:block">
        <div className="h-1 w-full bg-gradient-to-r from-[#0F5FDC] to-[#6B2FB5]" />
        <div className="border-b border-[#DFE4EC] px-6 py-6">
          <Link href={homeByRole[role]} className="block">
            <span className="text-xs font-bold uppercase tracking-[0.28em] text-[#0F5FDC]">NEXUS</span>
            <span className="mt-1 block text-lg font-bold tracking-tight text-[#172033]">Capability Intelligence</span>
            <span className="mt-2 block text-xs text-[#64748B]">{role === "leadership" ? "Leadership workspace" : role === "admin" ? "Talent operations" : "Engineering workspace"}</span>
          </Link>
        </div>
        <nav className="space-y-1 p-4">
          {items.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return <Link key={item.href} href={item.href} className={`block rounded-lg border-l-2 px-4 py-2.5 text-sm font-medium ${active ? "border-[#0F5FDC] bg-[#EEF5FF] text-[#0F5FDC]" : "border-transparent text-[#475569] hover:bg-[#F2F5FA] hover:text-[#172033]"}`}>{item.label}</Link>;
          })}
        </nav>
        <div className="absolute bottom-0 left-0 right-0 border-t border-[#DFE4EC] p-4">
          <div className="mb-3 rounded-lg bg-[#F2F5FA] px-3 py-2"><p className="text-[10px] font-bold uppercase tracking-widest text-[#64748B]">Workspace</p><p className="mt-1 truncate text-sm font-semibold capitalize text-[#172033]">{currentRole ?? role}</p></div>
          <button onClick={signOut} className="w-full rounded-lg border border-[#CBD5E1] px-3 py-2 text-left text-sm font-medium text-[#475569] hover:border-[#0F5FDC] hover:text-[#0F5FDC]">Sign out</button>
        </div>
      </aside>

      <div className="min-h-screen lg:ml-64">
        <header className="sticky top-0 z-10 border-b border-[#DFE4EC] bg-white/95 px-5 py-4 backdrop-blur sm:px-8">
          <div className="flex items-center justify-between">
            <div><p className="text-xs font-semibold uppercase tracking-widest text-[#64748B]">NEXUS / {role}</p><p className="mt-1 text-sm font-semibold text-[#172033]">Capability intelligence for better deployment decisions</p></div>
            <button onClick={signOut} className="rounded-lg px-3 py-2 text-sm font-medium text-[#64748B] hover:bg-[#F2F5FA] hover:text-[#172033] lg:hidden">Sign out</button>
          </div>
          <nav className="mt-4 flex gap-2 overflow-x-auto lg:hidden">{items.map((item) => <Link key={item.href} href={item.href} className={`whitespace-nowrap rounded-lg border px-3 py-2 text-xs font-medium ${pathname === item.href ? "border-[#0F5FDC] bg-[#EEF5FF] text-[#0F5FDC]" : "border-[#DFE4EC] bg-white text-[#64748B]"}`}>{item.label}</Link>)}</nav>
        </header>
        <main className="min-h-screen p-5 sm:p-8">{children}</main>
      </div>
    </div>
  );
}
