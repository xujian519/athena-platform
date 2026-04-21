<template>
  <footer class="footer">
    <div class="footer-container">
      <p>&copy; {{ currentYear }} Athena平台. 保留所有权利。</p>
      <div class="links">
        <a href="https://github.com/athena" target="_blank">GitHub</a>
        <a href="/docs">文档</a>
        <a href="/support">支持</a>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'

const currentYear = computed(() => new Date().getFullYear())
</script>

<style scoped>
.footer {
  background: #333;
  color: white;
  padding: 20px 0;
  margin-top: auto;
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.links {
  display: flex;
  gap: 20px;
}

.links a {
  color: white;
  text-decoration: none;
}

.links a:hover {
  text-decoration: underline;
}
</style>
