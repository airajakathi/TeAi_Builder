import { useCallback, useEffect, useState } from "react";
import { Check, ChevronDown, Folder, Loader2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import type {
  WorkspaceScopePayload,
  WorkspacesPayload,
} from "@/lib/types";
import { getHostApi } from "@/lib/runtime";
import { cn } from "@/lib/utils";
import {
  isAbsoluteWorkspacePath,
  projectNameFromPath,
  selectedProjectScope,
  shortWorkspacePath,
} from "@/lib/workspace";
import { fetchWorkspaceFolders } from "@/lib/api";

interface WorkspaceFolder {
  path: string;
  name: string;
}

export function WorkspaceProjectPicker({
  isHero,
  disabled,
  scope,
  defaultScope,
  controls,
  error,
  onChange,
  authToken,
}: {
  isHero: boolean;
  disabled?: boolean;
  scope: WorkspaceScopePayload | null;
  defaultScope: WorkspaceScopePayload | null;
  controls: WorkspacesPayload["controls"] | null;
  error?: string | null;
  onChange?: (scope: WorkspaceScopePayload) => void;
  authToken?: string;
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [pathDraft, setPathDraft] = useState("");
  const [pathError, setPathError] = useState<string | null>(null);
  const [pickingFolder, setPickingFolder] = useState(false);
  const [loadingFolders, setLoadingFolders] = useState(false);
  const [folders, setFolders] = useState<WorkspaceFolder[]>([]);
  const currentProjectScope = selectedProjectScope(scope, defaultScope);
  const projectLabel = currentProjectScope
    ? currentProjectScope.project_name || projectNameFromPath(currentProjectScope.project_path)
    : t("thread.composer.workspace.projectPlaceholder");
  const visible = isHero
    && !!defaultScope
    && !!onChange
    && controls?.can_change_project !== false;
  const hostApi = getHostApi();
  const nativeProjectPicker = !!hostApi;

  useEffect(() => {
    if (!open) return;
    setPathDraft(currentProjectScope?.project_path ?? "");
    setPathError(null);
  }, [currentProjectScope?.project_path, open]);

  useEffect(() => {
    if (!open) return;
    if (!defaultScope) return;
    let cancelled = false;
    setLoadingFolders(true);
    fetchWorkspaceFolders(authToken ?? "")
      .then((result) => {
        if (!cancelled) {
          setFolders(result.folders ?? []);
          setLoadingFolders(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFolders([]);
          setLoadingFolders(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [open, defaultScope]);

  useEffect(() => {
    if (error && visible) setOpen(true);
  }, [error, visible]);

  const resolveProjectPath = useCallback(
    (projectPath: string) => {
      const trimmed = projectPath.trim();
      if (!trimmed) return "";
      if (isAbsoluteWorkspacePath(trimmed)) return trimmed;
      const root = (scope ?? defaultScope)?.project_path ?? "";
      const normalizedRoot = root.replace(/\\/g, "/").replace(/\/+$/, "");
      const normalizedInput = trimmed.replace(/\\/g, "/").replace(/^\/+/, "");
      if (!normalizedRoot) return trimmed;
      return `${normalizedRoot}/${normalizedInput}`;
    },
    [defaultScope, scope],
  );

  const applyProjectPath = useCallback(
    (projectPath: string, projectName?: string) => {
      const base = scope ?? defaultScope;
      const resolved = resolveProjectPath(projectPath);
      if (!base || !onChange) return;
      if (!resolved || !isAbsoluteWorkspacePath(resolved)) {
        setPathError(t("workspace.dialog.absolutePathRequired"));
        return;
      }
      onChange({
        ...base,
        project_path: resolved,
        project_name: projectName || projectNameFromPath(resolved),
        restrict_to_workspace: base.access_mode === "restricted",
      });
      setPathError(null);
      setOpen(false);
    },
    [defaultScope, onChange, scope, t, resolveProjectPath],
  );

  const pickNativeFolder = useCallback(async () => {
    if (!hostApi || disabled) return;
    setPickingFolder(true);
    try {
      const picked = await hostApi.pickFolder();
      if (picked) applyProjectPath(picked);
    } catch (err) {
      setPathError((err as Error).message);
    } finally {
      setPickingFolder(false);
    }
  }, [applyProjectPath, disabled, hostApi]);

  if (!visible || !defaultScope || !onChange) return null;

  if (nativeProjectPicker) {
    return (
      <div className="flex items-center rounded-b-[28px] border-t border-border/25 bg-muted/60 px-4 py-1.5 dark:bg-white/[0.055]">
        <button
          type="button"
          disabled={disabled || pickingFolder}
          aria-label={t("thread.composer.workspace.projectAria")}
          title={currentProjectScope?.project_path}
          onClick={() => void pickNativeFolder()}
          className={cn(
            "inline-flex h-7 max-w-[18rem] items-center gap-2 rounded-full px-2.5",
            "text-[12px] font-medium text-muted-foreground/90 transition-colors",
            "hover:bg-background/70 hover:text-foreground disabled:pointer-events-none disabled:opacity-55",
            currentProjectScope && "text-foreground/82",
          )}
        >
          <Folder className={cn("h-3.5 w-3.5 shrink-0", currentProjectScope && "text-primary")} />
          <span className="truncate">{projectLabel}</span>
        </button>
        {pathError || error ? (
          <span role="alert" className="ml-2 truncate text-[11.5px] font-medium text-destructive">
            {pathError ?? error}
          </span>
        ) : null}
      </div>
    );
  }

  return (
    <div className="flex items-center rounded-b-[28px] border-t border-border/25 bg-muted/60 px-4 py-1.5 dark:bg-white/[0.055]">
      <DropdownMenu open={open} onOpenChange={setOpen}>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            disabled={disabled}
            aria-label={t("thread.composer.workspace.projectAria")}
            className={cn(
              "inline-flex h-7 max-w-[18rem] items-center gap-2 rounded-full px-2.5",
              "text-[12px] font-medium text-muted-foreground/90 transition-colors",
              "hover:bg-background/70 hover:text-foreground disabled:pointer-events-none disabled:opacity-55",
              currentProjectScope && "text-foreground/82",
            )}
          >
            <Folder className={cn("h-3.5 w-3.5 shrink-0", currentProjectScope && "text-primary")} />
            <span className="truncate">{projectLabel}</span>
            <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="start"
          side="bottom"
          sideOffset={8}
          className="max-h-80 w-[min(25rem,calc(100vw-2rem))] overflow-y-auto rounded-[22px]"
        >
          <DropdownMenuItem
            onSelect={() => applyProjectPath(defaultScope.project_path, defaultScope.project_name)}
            className="flex min-h-[48px] cursor-default gap-3 rounded-[16px] px-3 py-2.5 focus:bg-muted/55"
          >
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-[12px] bg-muted text-foreground/80">
              <Folder className="h-4 w-4" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-[13px] font-semibold text-foreground">
                {t("workspace.dialog.defaultProject")}
              </span>
              <span className="block truncate text-[11.5px] text-muted-foreground">
                {shortWorkspacePath(defaultScope.project_path)}
              </span>
            </span>
            {!currentProjectScope ? <Check className="h-4 w-4 text-foreground/80" /> : null}
          </DropdownMenuItem>
          <div className="my-1 h-px bg-border/45" />
          {loadingFolders ? (
            <div className="flex items-center gap-2 px-3 py-2 text-[12px] text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              <span>Loading projects…</span>
            </div>
          ) : (
            <div className="max-h-56 overflow-y-auto px-1.5 py-1.5">
              {folders.length === 0 ? (
                <p className="px-1 py-2 text-[12px] text-muted-foreground">No folders found</p>
              ) : (
                folders.map((folder) => {
                  const selected = currentProjectScope
                    ? currentProjectScope.project_path === folder.path
                    : false;
                  return (
                    <DropdownMenuItem
                      key={folder.path}
                      onSelect={() => applyProjectPath(folder.path, folder.name)}
                      className="flex min-h-[44px] gap-3 rounded-[16px] px-3 py-2.5 focus:bg-muted/55"
                    >
                      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-[12px] bg-muted text-foreground/80">
                        <Folder className="h-4 w-4" />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-[13px] font-semibold text-foreground">
                          {folder.name}
                        </span>
                        <span className="block truncate text-[11.5px] text-muted-foreground">
                          {shortWorkspacePath(folder.path)}
                        </span>
                      </span>
                      {selected ? <Check className="h-4 w-4 text-foreground/80" /> : null}
                    </DropdownMenuItem>
                  );
                })
              )}
            </div>
          )}
          <div className="my-1 h-px bg-border/45" />
          <div
            className="space-y-1.5 px-1.5 py-1.5"
            onKeyDown={(event) => {
              if (event.key !== "Escape") event.stopPropagation();
            }}
          >
            <form
              className="flex items-center gap-2"
              onSubmit={(event) => {
                event.preventDefault();
                applyProjectPath(pathDraft);
              }}
            >
              <Input
                value={pathDraft}
                disabled={disabled}
                onChange={(event) => {
                  setPathDraft(event.target.value);
                  setPathError(null);
                }}
                placeholder={t("workspace.dialog.manualPlaceholder")}
                aria-label={t("workspace.dialog.manual")}
                className={cn(
                  "h-9 rounded-full border-border/55 bg-background/80 px-3 text-[12.5px]",
                  "focus-visible:ring-1 focus-visible:ring-foreground/10 focus-visible:ring-offset-0",
                )}
              />
              <Button
                type="submit"
                disabled={disabled || !pathDraft.trim()}
                className="h-9 shrink-0 rounded-full px-3 text-[12px]"
              >
                {t("workspace.dialog.usePath")}
              </Button>
            </form>
            {pathError || error ? (
              <p role="alert" className="px-1 text-[11.5px] font-medium text-destructive">
                {pathError ?? error}
              </p>
            ) : null}
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
