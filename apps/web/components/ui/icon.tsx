const paths = {
  brand: <><path d="M4 5h6v6H4zM14 13h6v6h-6zM14 5h6v4h-6zM4 15h6v4H4z" /><path d="m10 11 4 2" /></>,
  document: <><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Z" /><path d="M14 3v6h6M8 13h8m-8 4h6" /></>,
  chat: <path d="M6 4h12a3 3 0 0 1 3 3v7a3 3 0 0 1-3 3h-6l-5 4v-4H6a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3Zm1 6h10M7 13h6" />,
  quote: <path d="M10 8H5v7h5v-4H7c0-2 1-3 3-4m9 1h-5v7h5v-4h-3c0-2 1-3 3-4" />,
  check: <path d="m5 12 4 4L19 6" />,
  arrow: <path d="M4 12h15m-6-6 6 6-6 6" />,
  external: <path d="M8 16 17 7M8 7h9v9" />,
  upload: <path d="M12 15V3m-4 4 4-4 4 4M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4" />,
  search: <><circle cx="10.5" cy="10.5" r="5.5" /><path d="m15 15 5 5" /></>,
  close: <path d="m6 6 12 12M18 6 6 18" />,
};

export function Icon({ name, size = 20 }: { name: keyof typeof paths; size?: number }) {
  return (
    <svg aria-hidden="true" focusable="false" width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round">
      {paths[name]}
    </svg>
  );
}
