// Conjunto de ícones em estilo linha (stroke 1.5, currentColor) usado em todo o
// app no lugar de emojis. Tamanho por prop `size`; herdam a cor do texto.

function Icon({ size = 18, className = "", strokeWidth = 1.5, children, ...props }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

// Marca: broto/sprout — crescimento e campo (agronomia).
export function Brandmark({ size = 22, className = "", strokeWidth = 1.6, ...props }) {
  return (
    <Icon size={size} strokeWidth={strokeWidth} className={className} {...props}>
      <path d="M7 20h10" />
      <path d="M10 20c5.5-2.5.8-6.4 3-10" />
      <path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4 2.8-.5 4.4 0 5.5.6z" />
      <path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z" />
    </Icon>
  );
}

export function IconExternal({ size = 15, className = "", ...props }) {
  return (
    <Icon size={size} className={className} {...props}>
      <path d="M15 3h6v6" />
      <path d="M10 14 21 3" />
      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
    </Icon>
  );
}

export function IconChevron({ size = 16, className = "", ...props }) {
  return (
    <Icon size={size} className={className} {...props}>
      <path d="m6 9 6 6 6-6" />
    </Icon>
  );
}

export function IconCheck({ size = 15, className = "", strokeWidth = 2, ...props }) {
  return (
    <Icon size={size} strokeWidth={strokeWidth} className={className} {...props}>
      <path d="M20 6 9 17l-5-5" />
    </Icon>
  );
}

export function IconAlert({ size = 15, className = "", ...props }) {
  return (
    <Icon size={size} className={className} {...props}>
      <path d="m10.29 3.86-8.18 14.14A1.5 1.5 0 0 0 3.4 20.5h17.2a1.5 1.5 0 0 0 1.29-2.5L13.71 3.86a1.5 1.5 0 0 0-2.42 0Z" />
      <path d="M12 9v4" />
      <path d="M12 17h.01" />
    </Icon>
  );
}

export function IconSend({ size = 18, className = "", ...props }) {
  return (
    <Icon size={size} className={className} {...props}>
      <path d="M22 2 11 13" />
      <path d="m22 2-7 20-4-9-9-4 20-7z" />
    </Icon>
  );
}
