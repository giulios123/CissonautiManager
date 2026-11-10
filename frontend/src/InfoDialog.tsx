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
 * Read-only modal. Focus enters the dialog on the close button, Tab stays inside, Escape closes,
 * and focus goes back to `returnFocusTo` when it closes. Render it only while it is open.
 */
export function InfoDialog({
  title,
  children,
  onClose,
  returnFocusTo,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  returnFocusTo?: RefObject<HTMLElement | null>;
}) {
  const t = useT();
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    closeRef.current?.focus();
    const target = returnFocusTo?.current;
    return () => target?.focus();
  }, [returnFocusTo]);

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.stopPropagation();
      onClose();
      return;
    }
    if (event.key !== "Tab") return;
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
        className="dialog-wide"
        ref={dialogRef}
        onKeyDown={onKeyDown}
      >
        <h2 id={titleId}>{title}</h2>
        <div>{children}</div>
        <div className="actions">
          <button type="button" className="secondary" ref={closeRef} onClick={onClose}>
            {t("common.close")}
          </button>
        </div>
      </div>
    </div>
  );
}
