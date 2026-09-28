import {defineConfig} from '@playwright/test'
export default defineConfig({testDir:'./e2e',fullyParallel:false,workers:1,use:{baseURL:'http://localhost:18080',headless:true,viewport:{width:1440,height:1050},screenshot:'only-on-failure'},reporter:'list',timeout:45000})
