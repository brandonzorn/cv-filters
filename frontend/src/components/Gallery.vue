<script setup lang="ts">
import { useGallery } from '../composables/useGallery';

const formatDate = (dateString: string) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleString();
};

const { images, isLoading, error, refresh } = useGallery();
</script>

<template>
  <div class="container py-5">
    <section id="gallery">
      <div class="row justify-content-center">
        <div class="col-md-8">
          <h2 class="h4 mb-4 text-center">Галерея обработанных фото</h2>
          <div v-if="isLoading" class="d-flex flex-column align-items-center justify-content-center py-5">
            <div class="spinner-border" role="status">
              <span class="visually-hidden">Загрузка изображений</span>
            </div>
          </div>
          <div v-else-if="error" class="alert alert-danger text-center">
            <p class="mb-2">Ошибка при загрузке списка.</p>
            <button class="btn btn-outline-danger btn-sm" @click="refresh">
              Попробовать снова
            </button>
          </div>
          <div v-else-if="images.length === 0" class="alert alert-info text-center">
            Список пуст. Загрузите первое изображение!
          </div>

          <div v-else class="row g-4">
            <div v-for="img in images" :key="img.id" class="col-12 col-lg-6">
              <div class="card h-100 shadow-sm">
                <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                  <span class="badge bg-success">{{ img.filter_type }}</span>
                  <small class="text-white-50">{{ formatDate(img.created_at) }}</small>
                </div>

                <div class="card-body">
                  <div class="row g-2">
                    <div class="col-6 d-flex flex-column align-items-center">
                      <p class="small text-center mb-1 fw-bold">Оригинал</p>
                      <img :src="img.original_url" class="img-fluid rounded border" alt="Оригинал" />
                    </div>
                    <div class="col-6 d-flex flex-column align-items-center">
                      <p class="small text-center mb-1 fw-bold text-primary">Результат</p>
                      <img :src="img.processed_url" class="img-fluid rounded border border-primary" alt="Результат" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>