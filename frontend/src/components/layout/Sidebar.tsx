"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { LayoutDashboard, FileText, MapPin, Search, PlusCircle, User, MessageSquare, Heart, Shield, LogOut } from "lucide-react";

const sidebarItemClass = "flex items-center gap-3 px-4 py-2 text-sm transition-none";
const activeClass = "font-bold text-text-primary border-l-[3px] border-text-primary pl-[13px]";
const inactiveClass = "font-normal text-text-muted hover:text-text-secondary pl-4";

export function Sidebar() {
  const pathname = usePathname();
  const { isCitizen, isAuthority, logout } = useAuth();

  const isActive = (path: string) => pathname === path || pathname.startsWith(path + '/');

  return (
    <aside className="fixed left-0 top-0 h-screen w-[240px] bg-surface-primary border-r border-border-light z-50 flex flex-col">
      <div className="p-6">
        <h1 className="text-lg font-extrabold tracking-tight text-text-primary">PEHEL NEO</h1>
        <p className="text-[10px] uppercase tracking-wider text-text-muted mt-1">CIVIC ACCOUNTABILITY PLATFORM</p>
      </div>
      <div className="hairline mx-4" />
      
      <nav className="flex-1 py-6 overflow-y-auto">
        <div className="mb-6">
          <p className="label-text px-4 mb-2">MAIN</p>
          <Link href="/dashboard" className={`${sidebarItemClass} ${isActive('/dashboard') ? activeClass : inactiveClass}`}>
            <LayoutDashboard size={16} /> DASHBOARD
          </Link>
          <Link href="/feed/for-you" className={`${sidebarItemClass} ${isActive('/feed/for-you') ? activeClass : inactiveClass}`}>
            <FileText size={16} /> FOR YOU
          </Link>
          <Link href="/nearby" className={`${sidebarItemClass} ${isActive('/nearby') ? activeClass : inactiveClass}`}>
            <MapPin size={16} /> NEARBY
          </Link>
          <Link href="/issues" className={`${sidebarItemClass} ${isActive('/issues') && !isActive('/issues/new') ? activeClass : inactiveClass}`}>
            <Search size={16} /> ISSUES
          </Link>
          <Link href="/issues/new" className={`${sidebarItemClass} ${isActive('/issues/new') ? activeClass : inactiveClass}`}>
            <PlusCircle size={16} /> REPORT ISSUE
          </Link>
        </div>

        {isCitizen && (
          <div className="mb-6">
            <div className="hairline mx-4 mb-4" />
            <p className="label-text px-4 mb-2">ME</p>
            <Link href="/me/issues" className={`${sidebarItemClass} ${isActive('/me/issues') ? activeClass : inactiveClass}`}>
              <User size={16} /> MY ISSUES
            </Link>
            <Link href="/me/comments" className={`${sidebarItemClass} ${isActive('/me/comments') ? activeClass : inactiveClass}`}>
              <MessageSquare size={16} /> MY COMMENTS
            </Link>
            <Link href="/me/supports" className={`${sidebarItemClass} ${isActive('/me/supports') ? activeClass : inactiveClass}`}>
              <Heart size={16} /> MY SUPPORTS
            </Link>
          </div>
        )}

        {isAuthority && (
          <div className="mb-6">
            <div className="hairline mx-4 mb-4" />
            <p className="label-text px-4 mb-2">AUTHORITY</p>
            <Link href="/authority" className={`${sidebarItemClass} ${isActive('/authority') ? activeClass : inactiveClass}`}>
              <Shield size={16} /> WORKSPACE
            </Link>
          </div>
        )}
      </nav>

      <div className="p-4 mt-auto">
        <div className="hairline mb-4" />
        <button onClick={logout} className={`${sidebarItemClass} ${inactiveClass} w-full text-left`}>
          <LogOut size={16} /> LOG OUT
        </button>
        <p className="label-text px-4 mt-4">KANPUR PILOT</p>
        <p className="label-text px-4">5 WARDS ACTIVE</p>
      </div>
    </aside>
  );
}