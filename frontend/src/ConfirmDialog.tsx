import {
  useEffect,
  useId,
  useRef,
  type KeyboardEvent,
  type ReactNode,
  type RefObject,
} from "react";

import { useT } from "./i18n";

const TABBABLE = 'button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])';

/**
 * Modal confirmation. Focus starts on the harmless choice, Tab stays inside the dialog, Escape
 * cancels, and focus goes back to `returnFocusTo` when the dialog closes. Render it only while it
 * is open.
 */
export function ConfirmDialog({
  title,
  children,
  confirmLabel,
  cancelLabel,
  working = false,
  cancelDisabled = false,
  confirmDisabled = false,
  error = null,
  onConfirm,
  onCancel,
  returnFocusTo,
}: {
  title: string;
  children: ReactNode;
  confirmLabel: string;
  cancelLabel?: string;
  working?: boolean;
  cancelDisabled?: boolean;
  confirmDisabled?: boolean;
  error?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
  returnFocusTo?: RefObject<HTMLElement | null>;
}) {
  const t = useT();
  const titleId = useId();
  const textId = useId();
  const cancelRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    cancelRef.current?.focus();
    const target = returnFocusTo?.current;
    return () => target?.focus();
  }, [returnFocusTo]);

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.stopPropagation();
      if (!cancelDisabled) onCancel();
      return;
    }
    if (event.key !== "Tab") return;
    // Every enabled control, not only buttons: a dialog can hold a field (the void reason).
    const controls = [...(dialogRef.current?.querySelectorAll<HTMLElement>(TABBABLE) ?? [])].filter(
      (element) => !element.hasAttribute("disabled"),
    );
    const first = controls[0];
    const last = controls[controls.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first?.focus();
    }
  }

  return (
    <div className="backdrop">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={textId}
        ref={dialogRef}
        onKeyDown={onKeyDown}
      >
        <h2 id={titleId}>{title}</h2>
        <div id={textId}>{children}</div>
        {error && (
          <p role="alert" className="notice error">
            {error}
          </p>
        )}
        <div className="actions">
          <button
            type="button"
            className="secondary"
            ref={cancelRef}
            disabled={cancelDisabled}
            onClick={onCancel}
          >
            {cancelLabel ?? t("dialog.back")}
          </button>
          <button
            type="button"
            className="danger"
            onClick={onConfirm}
            disabled={working || confirmDisabled}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
