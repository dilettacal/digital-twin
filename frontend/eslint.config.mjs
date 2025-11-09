// frontend/eslint.config.mjs
import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import reactPlugin from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import jsxA11y from "eslint-plugin-jsx-a11y";
import ts from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import globals from "globals";

export default [
  js.configs.recommended,
  prettier,
  {
    files: ["**/*.{js,jsx,ts,tsx}"],
    ignores: [
      "node_modules/",
      ".next/",
      "out/",
      "dist/",
      "build/",
      "coverage/"
    ],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: { jsx: true }
      },
      globals: {
        ...globals.browser,
        ...globals.node
      }
    },
    plugins: {
      react: reactPlugin,
      "react-hooks": reactHooks,
      "jsx-a11y": jsxA11y,
      "@typescript-eslint": ts
    },
    rules: {
      "no-undef": "off",
      "react/react-in-jsx-scope": "off",
      "react/prop-types": "off",
      "no-prototype-builtins": "off",
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-unused-expressions": "off",
      ...reactHooks.configs.recommended.rules
    },
    settings: {
      react: { version: "detect" }
    }
  }
];
