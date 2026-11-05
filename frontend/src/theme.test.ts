import css from "./styles.css?raw";

function rootBlock(): string {
  const match = css.match(/:root\s*{([^}]*)}/);
  if (!match) throw new Error(":root block not found");
  return match[1];
}

function token(name: string): string {
  const match = rootBlock().match(new RegExp(`--${name}:\\s*(#[0-9a-fA-F]{6})`));
  if (!match) throw new Error(`token --${name} not found`);
  return match[1];
}

function luminance(hex: string): number {
  const channels = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
  const [r, g, b] = channels.map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

describe("theme tokens", () => {
  it.each([
    ["color-text", "color-bg"],
    ["color-text", "color-surface"],
    ["color-text", "color-paper"],
    ["color-text-muted", "color-bg"],
    ["color-text-muted", "color-paper"],
    ["color-text-muted", "color-surface"],
    ["color-on-dark", "color-primary-dark"],
    ["color-on-primary", "color-danger"],
    ["color-on-cta", "color-cta-hover"],
    ["color-text", "color-cta-soft"],
    ["color-heading", "color-bg"],
    ["color-primary", "color-bg"],
    ["color-on-primary", "color-primary"],
    ["color-on-cta", "color-cta"],
    ["color-on-danger", "color-danger"],
    ["color-error", "color-bg"],
    ["color-error", "color-error-bg"],
    ["color-text", "color-success-bg"],
    ["color-primary", "color-primary-soft"],
    ["status-pending-fg", "status-pending-bg"],
    ["status-confirmed-fg", "status-confirmed-bg"],
    ["status-expired-fg", "status-expired-bg"],
    ["status-cancel-fg", "status-cancel-bg"],
    ["status-refunded-fg", "status-refunded-bg"],
  ])("%s on %s reaches AA for normal text", (fg, bg) => {
    expect(contrast(token(fg), token(bg))).toBeGreaterThanOrEqual(4.5);
  });

  it.each([
    ["color-border-strong", "color-bg"],
    ["color-primary", "color-cta"],
  ])("%s on %s reaches 3:1 for borders and focus", (fg, bg) => {
    expect(contrast(token(fg), token(bg))).toBeGreaterThanOrEqual(3);
  });

  it("never uses the amber for text or focus, only as a fill or decoration", () => {
    expect(contrast(token("color-cta"), token("color-bg"))).toBeLessThan(3);
    // List bullets are decoration, not text.
    const outsideRoot = css.replace(/:root\s*{[^}]*}/, "").replace(/::marker\s*{[^}]*}/g, "");
    expect(outsideRoot).not.toMatch(
      /(^|[\s;{])(color|outline(-color)?):[^;]*var\(--color-(cta|accent)\)/m,
    );
  });

  it("has no colored side stripes on cards, notices or badges", () => {
    expect(css).not.toMatch(/border-(left|right)(-width)?:\s*([2-9]|\d{2,})px/);
  });

  it("defines colors only in :root", () => {
    const outsideRoot = css.replace(/:root\s*{[^}]*}/, "").replace(/\/\*[\s\S]*?\*\//g, "");
    expect(outsideRoot).not.toMatch(/#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(/);
  });
});
