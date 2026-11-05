/** True when the page runs inside an iframe, such as the event site on Google Sites. */
export function isInFrame(): boolean {
  try {
    return window.self !== window.top;
  } catch {
    // Reading window.top can throw across origins, which only happens inside a frame.
    return true;
  }
}
