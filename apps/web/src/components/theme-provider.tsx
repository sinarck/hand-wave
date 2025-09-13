"use client";

import * as React from "react";
import { ThemeProvider as NextThemesProvider } from "next-themes";

/**
 * Thin wrapper around `NextThemesProvider` that forwards all received props and renders `children`.
 *
 * This client-side component mirrors the API of `NextThemesProvider` — any props passed to `ThemeProvider`
 * are forwarded to `NextThemesProvider`.
 */
export function ThemeProvider({
	children,
	...props
}: React.ComponentProps<typeof NextThemesProvider>) {
	return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
}
