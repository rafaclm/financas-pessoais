<script setup lang="ts">
import { RouterView } from "vue-router"
</script>

<template>
  <div class="auth-shell">
    <!-- Círculos decorativos de fundo -->
    <div class="bg-deco">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>

    <div class="auth-content">
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.auth-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
  background: var(--bg-base);
  position: relative;
  overflow: hidden;
}

.auth-content {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 440px;
}

/* Orbes decorativos animados */
.bg-deco {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 1;
}
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
  animation: flutuar 20s infinite ease-in-out;
}
.orb-1 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, #A78BFA, transparent);
  top: -100px; left: -100px;
}
.orb-2 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, #DDB7FF, transparent);
  bottom: -150px; right: -150px;
  animation-delay: -5s;
}
.orb-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #B0C6FF, transparent);
  top: 40%; right: 20%;
  animation-delay: -10s;
}

@keyframes flutuar {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}
</style>