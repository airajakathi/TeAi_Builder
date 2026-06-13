import { Menu, Moon, PanelRight, Sun } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ThreadHeaderProps {
  title: string;
  onToggleSidebar: () => void;
  theme: "light" | "dark";
  onToggleTheme: () => void;
  hideSidebarToggleForHostChrome?: boolean;
  hostChromeTitleInset?: boolean;
  hideThemeButton?: boolean;
  minimal?: boolean;
  promptNavigatorAction?: ReactNode;
  sessionInfoAction?: ReactNode;
  canvasOpen?: boolean;
  canvasHasContent?: boolean;
  onToggleCanvas?: () => void;
}

export function ThreadHeader({
  title,
  onToggleSidebar,
  theme,
  onToggleTheme,
  hideSidebarToggleForHostChrome = false,
  hostChromeTitleInset = false,
  hideThemeButton = false,
  minimal = false,
  promptNavigatorAction,
  sessionInfoAction,
  canvasOpen = false,
  canvasHasContent = false,
  onToggleCanvas,
}: ThreadHeaderProps) {
  const { t } = useTranslation();

  return (
    <div
      className={cn(
        "relative z-10 flex items-center justify-between gap-3 px-3 py-2",
        minimal && "h-11",
        !minimal && hostChromeTitleInset && "lg:pl-[128px]",
      )}
    >
      <div className="relative flex min-w-0 items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          aria-label={t("thread.header.toggleSidebar")}
          onClick={onToggleSidebar}
          className={cn(
            "h-7 w-7 rounded-md text-muted-foreground hover:bg-accent/35 hover:text-foreground",
            hideSidebarToggleForHostChrome && "lg:hidden",
          )}
        >
          <Menu className="h-3.5 w-3.5" />
        </Button>
        {!minimal ? (
          <div className="flex min-w-0 items-center rounded-md px-1.5 py-1 text-[12px] font-medium text-muted-foreground">
            <span className="max-w-[min(60vw,32rem)] truncate">{title}</span>
          </div>
        ) : null}
      </div>

      <div className="ml-auto flex shrink-0 items-center gap-1">
        {sessionInfoAction}
        {promptNavigatorAction}
        {onToggleCanvas ? (
          <div className="relative">
            <Button
              variant="ghost"
              size="icon"
              aria-label={canvasOpen ? "Close canvas panel" : "Open canvas panel"}
              onClick={onToggleCanvas}
              className={cn(
                "host-no-drag h-8 w-8 rounded-full hover:bg-accent/40",
                canvasOpen
                  ? "text-foreground"
                  : "text-muted-foreground/85 hover:text-foreground",
              )}
            >
              <PanelRight className="h-4 w-4" />
            </Button>
            {canvasHasContent && !canvasOpen ? (
              <span
                aria-hidden
                className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-blue-500"
              />
            ) : null}
          </div>
        ) : null}
        {!hideThemeButton ? (
          <ThemeButton
            theme={theme}
            onToggleTheme={onToggleTheme}
            label={t("thread.header.toggleTheme")}
          />
        ) : null}
      </div>

      {!minimal ? (
        <div aria-hidden className="pointer-events-none absolute inset-x-0 top-full h-4" />
      ) : null}
    </div>
  );
}

function ThemeButton({
  theme,
  onToggleTheme,
  label,
  className,
}: {
  theme: "light" | "dark";
  onToggleTheme: () => void;
  label: string;
  className?: string;
}) {
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={label}
      onClick={onToggleTheme}
      className={cn(
        "host-no-drag h-8 w-8 rounded-full text-muted-foreground/85 hover:bg-accent/40 hover:text-foreground",
        className,
      )}
    >
      {theme === "dark" ? (
        <Sun className="h-4 w-4" />
      ) : (
        <Moon className="h-4 w-4" />
      )}
    </Button>
  );
}
