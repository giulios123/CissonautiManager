import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { setCurrentLocale } from "./i18n/locale";

// A test that renders in English must not leak the language into the next one.
afterEach(() => setCurrentLocale("it"));
