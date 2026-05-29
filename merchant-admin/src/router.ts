import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import DashboardView from './views/DashboardView.vue'
import ModuleView from './views/ModuleView.vue'
import ProductionView from './views/ProductionView.vue'
import CashierView from './views/CashierView.vue'
import StoreView from './views/StoreView.vue'
import ScreenView from './views/ScreenView.vue'
import ReportsView from './views/ReportsView.vue'
import PlatformView from './views/PlatformView.vue'

export type AdminRouteMeta = {
  title: string
  crumb: string
  description: string
}

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'dashboard',
    component: DashboardView,
    meta: {
      title: '现场等餐全局掌控',
      crumb: '首页 / 经营概览',
      description: '发号、队列、收银和菜品的日常总览'
    } satisfies AdminRouteMeta
  },
  {
    path: '/queue',
    name: 'queue',
    component: DashboardView,
    meta: {
      title: '队列管理',
      crumb: '队列 / 号码管理',
      description: '查看队列、打开号码详情、推进状态和处理异常'
    } satisfies AdminRouteMeta
  },
  {
    path: '/production',
    name: 'production',
    component: ProductionView,
    meta: {
      title: '制作工作台',
      crumb: '工作台 / 制作',
      description: '聚焦待制作、制作中和已叫号号码'
    } satisfies AdminRouteMeta
  },
  {
    path: '/cashier',
    name: 'cashier',
    component: CashierView,
    meta: {
      title: '收银记账',
      crumb: '工作台 / 收银',
      description: '处理待结账号码、收款确认和完成释放'
    } satisfies AdminRouteMeta
  },
  {
    path: '/store',
    name: 'store',
    component: StoreView,
    meta: {
      title: '门店管理',
      crumb: '设置 / 门店',
      description: '维护营业状态、营业时间、地址和排号规则'
    } satisfies AdminRouteMeta
  },
  {
    path: '/dishes',
    name: 'dishes',
    component: ModuleView,
    meta: {
      title: '菜品管理',
      crumb: '设置 / 菜品',
      description: '维护分类、价格和上下架状态'
    } satisfies AdminRouteMeta
  },
  {
    path: '/staff',
    name: 'staff',
    component: ModuleView,
    meta: {
      title: '员工权限',
      crumb: '设置 / 员工',
      description: '管理员工账号、角色和启停用状态'
    } satisfies AdminRouteMeta
  },
  {
    path: '/platform',
    name: 'platform',
    component: PlatformView,
    meta: {
      title: '平台审核',
      crumb: '平台 / 审核',
      description: '审核商户入驻、门店资料和套餐权限'
    } satisfies AdminRouteMeta
  },
  {
    path: '/screen',
    name: 'screen',
    component: ScreenView,
    meta: {
      title: '大屏叫号',
      crumb: '展示 / 大屏',
      description: '面向店内横屏展示当前叫号和等待队列'
    } satisfies AdminRouteMeta
  },
  {
    path: '/reports',
    name: 'reports',
    component: ReportsView,
    meta: {
      title: '数据统计',
      crumb: '经营 / 统计',
      description: '查看发号、完成、收银和平均等待数据'
    } satisfies AdminRouteMeta
  },
  {
    path: '/settings',
    name: 'settings',
    component: ModuleView,
    meta: {
      title: '系统设置',
      crumb: '设置 / 系统',
      description: '维护基础配置、公告和功能开关'
    } satisfies AdminRouteMeta
  }
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})
