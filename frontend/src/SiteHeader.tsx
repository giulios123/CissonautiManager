import { useState } from "react";
import { Link } from "react-router-dom";
import logoUrl from "./assets/logo-cissone.png";
import { isInFrame } from "./frame";

export const EVENT_NAME = "Cissonauti Summer Camp";

type Props = {
  /** Inside the event site's iframe: name only, no logo, so the site header is not repeated. */
  compact?: boolean;
};

export function SiteHeader({ compact = isInFrame() }: Props) {
  const [logoFailed, setLogoFailed] = useState(false);

  if (compact) {
    return (
      <header className="site-header compact">
        <p className="site-name">{EVENT_NAME}</p>
      </header>
    );
  }

  return (
    <header className="site-header">
      <Link to="/" className="site-brand">
        {!logoFailed && (
          <img
            src={logoUrl}
            alt="Cissone"
            width={160}
            height={30}
            onError={() => setLogoFailed(true)}
          />
        )}
        <span className="site-name">{EVENT_NAME}</span>
      </Link>
    </header>
  );
}
