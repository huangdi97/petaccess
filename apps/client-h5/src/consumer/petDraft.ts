export interface PetDraft {
  display_name: string;
  species: string;
  breed_text: string;
  weight_kg: string;
  shoulder_height_cm: string;
}

export function createEmptyPetDraft(): PetDraft {
  return {
    display_name: "",
    species: "dog",
    breed_text: "",
    weight_kg: "",
    shoulder_height_cm: "",
  };
}
