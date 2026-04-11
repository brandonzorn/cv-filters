import { ref } from "vue";
import { postImage } from "../scripts/api";

export function useUpload() {

    const selectedFile = ref<File | null>(null);
    const filterType = ref<string>('grayscale');

    const isUploading = ref(false);
    const error = ref<string | null>(null);

    let controller: AbortController | null = null;

    function handleFileChange(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files.length > 0) {
            selectedFile.value = target.files[0];
        }
    };

    async function uploadImage() {
        controller?.abort();
        controller = new AbortController();

        if (!selectedFile.value) return;

        try {
            isUploading.value = true;
            error.value = null;

            await postImage(selectedFile.value, filterType.value);

            selectedFile.value = null;
        } catch (e: any) {
            if (e?.name !== "AbortError") {
                error.value = e?.message ?? "Неизвестная ошибка";
                console.error("Ошибка при загрузке изображения:", e);
            }
        } finally {
            isUploading.value = false;
        }
    }

    return {
        selectedFile,
        filterType,
        isUploading,
        error,
        handleFileChange,
        uploadImage,
    }
}