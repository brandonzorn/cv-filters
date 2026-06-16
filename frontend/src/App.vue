<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { getApiStatus } from './scripts/api';

const apiStatus = ref<string>("fetching");

async function checkApiStatus() {
  try {
    apiStatus.value = await getApiStatus();
  } catch (e) {
    console.error("Ошибка при проверке статуса API", e);
    apiStatus.value = "offline";
  }
}

function statusToColor(): string {
  switch (apiStatus.value) {
    case "running":
      return "success";
    case "offline":
      return "danger";
    default:
      return "warning";
  }
}

function statusToText(): string {
  switch (apiStatus.value) {
    case "running":
      return "В сети";
    case "offline":
      return "Оффлайн";
    default:
      return "Проверка...";
  }
}

onMounted(checkApiStatus);
</script>

<template>
  <nav class="navbar navbar-expand-lg bg-body-tertiary">
    <div class="container-fluid">
      <RouterLink class="navbar-brand d-flex align-items-center" to="/">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
          class="me-1 text-emphasis-color">
          <rect width="18" height="18" x="3" y="3" rx="2" ry="2" />
          <circle cx="9" cy="9" r="2" />
          <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21" />
          <line x1="19" y1="2" x2="19" y2="6" />
          <line x1="17" y1="4" x2="21" y2="4" />
        </svg>
        <span class="text-truncate d-none d-sm-block">Фильтрация изображений</span>
      </RouterLink>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
        aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarNav">
        <ul class="navbar-nav">
          <li class="nav-item">
            <RouterLink class="nav-link" exact-active-class="active" to="/">Загрузка изображений</RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink class="nav-link" exact-active-class="active" to="/gallery">Галерея</RouterLink>
          </li>
          <li class="nav-item">
            <RouterLink class="nav-link" exact-active-class="active" to="/about">О проекте</RouterLink>
          </li>
        </ul>

        <div class="d-flex align-items-center border-start ps-lg-3 mt-3 mt-lg-0">
          <small :class="`text-${statusToColor()}`">{{ statusToText() }}</small>
        </div>
      </div>
    </div>
  </nav>

  <main>
    <RouterView />
  </main>
</template>
