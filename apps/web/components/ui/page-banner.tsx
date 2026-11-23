import { Icon } from "./icon";

export function PageBanner({ title, description, variant }: {
  title: string;
  description: string;
  variant: "chat" | "documents";
}) {
  return (
    <header className="page-banner">
      <div className="banner-copy">
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      <div className="banner-figure" aria-hidden="true">
        <div className="banner-grid" />
        <div className="banner-connector" />
        <div className="banner-card first"><Icon name={variant === "chat" ? "chat" : "upload"} size={40} /></div>
        <div className="banner-card second"><Icon name="document" size={42} /></div>
        <div className="banner-pin"><Icon name={variant === "chat" ? "quote" : "check"} size={19} /></div>
      </div>
    </header>
  );
}
