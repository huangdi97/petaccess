/**
 * 平台适配层（design #29：平台差异集中到 adapter/platform，不散落业务页面）。
 * uni-app x 端的 storage 与 API 基址配置。
 */
import { configureApi } from "@petaccess/client-core";

// HBuilderX 运行环境内置 uni 全局对象；TS 编译在 CLI 侧仅做类型提示
declare const uni: {
  getStorageSync(key: string): string;
  setStorageSync(key: string, value: string): void;
  removeStorageSync(key: string): void;
};

export const uniStorage = {
  get: (k: string): string | undefined => {
    const v = uni.getStorageSync(k);
    return v === "" ? undefined : v;
  },
  set: (k: string, v: string): void => {
    uni.setStorageSync(k, v);
  },
  remove: (k: string): void => {
    uni.removeStorageSync(k);
  },
};

export function uniRequestBase(): void {
  // #ifdef H5
  configureApi("/api/v1");
  // #endif
  // #ifndef H5
  configureApi("http://127.0.0.1:8000/api/v1");
  // #endif
}
