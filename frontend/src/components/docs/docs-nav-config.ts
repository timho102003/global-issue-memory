import {
  BookOpen,
  UserPlus,
  Terminal,
  Search,
  PlugZap,
  KeyRound,
  FileCode,
  Layers,
  GitBranch,
  HelpCircle,
  type LucideIcon,
} from "lucide-react";

export interface DocsNavItem {
  title: string;
  href?: string;
  icon: LucideIcon;
  children?: DocsNavLeaf[];
}

export interface DocsNavLeaf {
  title: string;
  href: string;
  icon: LucideIcon;
}

export const docsNavConfig: DocsNavItem[] = [
  {
    title: "Getting Started",
    href: "/docs/getting-started",
    icon: BookOpen,
    children: [
      { title: "Sign Up", href: "/docs/getting-started/sign-up", icon: UserPlus },
      { title: "Add MCP Server", href: "/docs/getting-started/add-mcp-server", icon: Terminal },
      { title: "Find Plugin", href: "/docs/getting-started/find-plugin", icon: Search },
      { title: "Verify Installation", href: "/docs/getting-started/verify-installation", icon: PlugZap },
      { title: "Authentication", href: "/docs/getting-started/authentication", icon: KeyRound },
      { title: "CLAUDE.md Setup", href: "/docs/getting-started/claude-md-setup", icon: FileCode },
    ],
  },
  {
    title: "How It Works",
    href: "/docs/how-it-works",
    icon: Layers,
    children: [
      { title: "System Design", href: "/docs/how-it-works/system-design", icon: Layers },
      { title: "Issue Lifecycle", href: "/docs/how-it-works/issue-lifecycle", icon: GitBranch },
    ],
  },
  {
    title: "Troubleshooting",
    href: "/docs/troubleshooting",
    icon: HelpCircle,
  },
];

/**
 * Returns a flat ordered list of all leaf pages for prev/next navigation.
 */
export function getAllLeafPages(): { title: string; href: string }[] {
  const pages: { title: string; href: string }[] = [];
  for (const item of docsNavConfig) {
    if (item.children) {
      for (const child of item.children) {
        pages.push({ title: child.title, href: child.href });
      }
    } else if (item.href) {
      pages.push({ title: item.title, href: item.href });
    }
  }
  return pages;
}

/**
 * Finds the parent nav item for a given path.
 */
export function findParent(pathname: string): DocsNavItem | null {
  for (const item of docsNavConfig) {
    if (item.children?.some((child) => child.href === pathname)) {
      return item;
    }
  }
  return null;
}

/**
 * Builds breadcrumb segments for a given path.
 */
export function buildBreadcrumbs(
  pathname: string
): { title: string; href: string }[] {
  const crumbs: { title: string; href: string }[] = [
    { title: "Docs", href: "/docs" },
  ];

  for (const item of docsNavConfig) {
    if (item.href === pathname) {
      crumbs.push({ title: item.title, href: item.href });
      return crumbs;
    }
    if (item.children) {
      for (const child of item.children) {
        if (child.href === pathname) {
          if (item.href) {
            crumbs.push({ title: item.title, href: item.href });
          }
          crumbs.push({ title: child.title, href: child.href });
          return crumbs;
        }
      }
      if (item.href === pathname) {
        crumbs.push({ title: item.title, href: item.href });
        return crumbs;
      }
    }
  }

  return crumbs;
}
