"use client";
import { useCallback, useEffect, useState } from "react";
import { getFloodStatus } from "./api";
import type { FloodStatusResponse } from "./types";
export type DataState = "loading" | "success" | "error";
export function useFloodData() { const [state, setState] = useState<DataState>("loading"); const [data, setData] = useState<FloodStatusResponse>(); const refresh = useCallback(async () => { setState("loading"); try { setData(await getFloodStatus()); setState("success"); } catch { setState("error"); } }, []); useEffect(() => { let active = true; getFloodStatus().then(value => { if (active) { setData(value); setState("success"); } }).catch(() => { if (active) setState("error"); }); return () => { active = false; }; }, []); return { state, data, refresh }; }
