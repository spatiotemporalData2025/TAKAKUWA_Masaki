import type { AppProps } from "next/app";
import "maplibre-gl/dist/maplibre-gl.css";
import "../styles/globals.css";

export default function MyApp({ Component, pageProps }: AppProps) {
  return <Component {...pageProps} />;
}
