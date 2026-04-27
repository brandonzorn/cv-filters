import { onMounted, ref, watch } from "vue";
import { getFilters, postImage } from "../scripts/api";

export function useUpload() {

    const selectedFile = ref<File | null>(null);
    const selectedFilterIndex = ref<number | null>(null);
    const extraParams = ref<Record<string, any>>({});

    const filters = ref<string[]>([]);

    const isUploading = ref(false);
    const error = ref<string | null>(null);

    let controller: AbortController | null = null;

    watch(selectedFilterIndex, (newIdx) => {
        extraParams.value = {
            kernel_size: 15,
            threshold1: 100,
            threshold2: 200
        };
    });

    async function fetchFilters() {
        filters.value = await getFilters();
        selectedFilterIndex.value = filters.value.length > 0 ? 0 : null;
    }

    function handleFileChange(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files.length > 0) {
            selectedFile.value = target.files[0];
        }
    };

    function getSelectedFilter(): string | null {
        if (selectedFilterIndex.value === null) {
            return null;
        }
        return filters.value[selectedFilterIndex.value];
    }

    async function uploadImage() {
        controller?.abort();
        controller = new AbortController();

        if (!selectedFile.value) return;

        try {
            isUploading.value = true;
            error.value = null;

            if (typeof (selectedFilterIndex.value) !== "number") {
                throw new Error(`selectedFilterIndex must be a number, got ${typeof (selectedFilterIndex.value)}`);
            }

            const paramsJson = JSON.stringify(extraParams.value);
            await postImage(selectedFile.value, filters.value[selectedFilterIndex.value], paramsJson, controller.signal);
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

    onMounted(fetchFilters);

    return {
        selectedFile,
        filters,
        selectedFilterIndex,
        extraParams,
        isUploading,
        error,
        getSelectedFilter,
        handleFileChange,
        uploadImage,
    }
}