import { createApp } from "vue"
import { createPinia } from "pinia"
import PrimeVue from "primevue/config"
import Aura from "@primevue/themes/aura"
import ToastService from "primevue/toastservice"
import ConfirmationService from "primevue/confirmationservice"
import Tooltip from "primevue/tooltip"
import "primeicons/primeicons.css"
import "./styles/global.css"
import "./styles/lumina-polish.css"

import App from "./App.vue"
import router from "./router"
import { useAuthStore } from "./stores/auth"

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

const authStore = useAuthStore()
authStore.init()

app.use(router)

app.use(PrimeVue, {
  theme: {
    preset: Aura,
    options: {
      darkModeSelector: ".theme-dark",
      cssLayer: false,
    }
  }
})
app.use(ToastService)
app.use(ConfirmationService)
app.directive("tooltip", Tooltip)

app.mount("#app")