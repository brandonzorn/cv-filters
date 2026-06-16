import { onBeforeUnmount, onMounted, ref } from "vue";
import type { ImageResponse } from "../scripts/models";
import { getImages } from "../scripts/api";

export function useGallery() {
    const images = ref<ImageResponse[]>([]);
    const isLoading = ref(false);
    const error = ref<string | null>(null);

    let controller: AbortController | null = null;

    async function refresh() {
        controller?.abort();
        controller = new AbortController();

        try {
            isLoading.value = true;
            error.value = null;

            images.value = await getImages(controller.signal);
        } catch (e: any) {
            if (e?.name !== "AbortError") {
                error.value = e?.message ?? "Неизвестная ошибка";
                console.error("Ошибка при загрузке списка:", e);
            }
        } finally {
            isLoading.value = false;
        }
    };

    function stop() {
        controller?.abort();
    }

    onMounted(refresh);
    onBeforeUnmount(stop);

    return {
        images,
        isLoading,
        error,
        refresh,
    };
}
