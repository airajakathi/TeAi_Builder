import { useRef, useEffect } from "react";

type FileMeta = {
  path: string;
  language?: string | null;
};

type Props = {
  files: FileMeta[];
  value?: string;
  onChange?: (next: string) => void;
  onSelectFile?: (file: FileMeta) => void;
  height?: number;
  readOnly?: boolean;
};

export function MonacoEditor({
  files,
  value = "",
  onChange,
  onSelectFile,
  height = 520,
  readOnly = false,
}: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const editorRef = useRef<unknown>(null);
  const selected = files[0] ?? null;

  useEffect(() => {
    if (!containerRef.current) return;
    let disposed = false;

    const init = async () => {
      const [{ editor }] = await Promise.all([
        import("monaco-editor"),
      ]);

      if (disposed || !containerRef.current) return;

      const instance = editor.create(containerRef.current, {
        value,
        language: selected?.language ?? "plaintext",
        theme: "vs",
        readOnly,
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 13,
        lineNumbers: "on",
        scrollBeyondLastLine: false,
        wordWrap: "on",
      });

      editorRef.current = instance;
      instance.onDidChangeModelContent(() => {
        onChange?.(instance.getValue());
      });
    };

    init();

    return () => {
      disposed = true;
      if (editorRef.current && typeof (editorRef.current as { dispose?: () => void }).dispose === "function") {
        (editorRef.current as { dispose: () => void }).dispose();
      }
    };
  }, [selected?.path, selected?.language, readOnly]);

  useEffect(() => {
    if (!editorRef.current) return;
    const instance = editorRef.current as { setValue: (value: string) => void; getValue: () => string };
    if (instance.getValue() !== value) {
      instance.setValue(value);
    }
  }, [value]);

  return (
    <div
      className="flex flex-col rounded-lg border border-gray-200 bg-white"
      style={{ height }}
    >
      <div className="flex items-center justify-between border-b border-gray-200 bg-gray-50 px-3 py-2">
        <div className="text-sm font-medium text-gray-800">Editor</div>
        <div className="text-xs text-gray-500">Monaco</div>
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
        <div ref={containerRef} className="flex-1" />
      </div>
    </div>
  );
}
