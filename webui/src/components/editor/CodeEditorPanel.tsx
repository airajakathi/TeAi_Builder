import { useMemo } from "react";

type FileMeta = {
  path: string;
  language?: string | null;
};

type Props = {
  files: FileMeta[];
  value?: string;
  onSelectFile?: (file: FileMeta) => void;
  height?: number;
};

export function CodeEditorPanel({
  files,
  value = "",
  onSelectFile,
  height = 520,
}: Props) {
  const selected = useMemo(() => files[0] ?? null, [files]);

  return (
    <div
      className="flex flex-col rounded-lg border border-gray-200 bg-gray-50"
      style={{ height }}
    >
      <div className="flex items-center justify-between border-b border-gray-200 bg-white px-3 py-2">
        <div className="text-sm font-medium text-gray-800">Editor preview</div>
        <div className="text-xs text-gray-500">Monaco integration placeholder</div>
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div className="w-56 overflow-y-auto border-r border-gray-200 bg-white">
          {selected ? (
            <button
              type="button"
              className="flex w-full items-center gap-2 border-b border-gray-100 px-3 py-2 text-left text-sm text-gray-900"
              onClick={() => onSelectFile?.(selected)}
            >
              <span className="truncate">{selected.path}</span>
            </button>
          ) : (
            <div className="px-3 py-2 text-sm text-gray-500">No files</div>
          )}
        </div>
        <div className="flex-1 whitespace-pre-wrap break-words p-3 text-sm text-gray-800">
          {value || "Select a file to view its contents."}
        </div>
      </div>
    </div>
  );
}
