<template>
  <div id="app">
    <NavBar />
    <main class="min-h-screen">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router';
import NavBar from '@/components/NavBar.vue';
</script>

<style>
@import '@/assets/styles/main.css';
</style>
