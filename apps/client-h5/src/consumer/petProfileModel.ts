export interface PetDraft {
  display_name: string;
  species: string;
  breed_text: string;
  weight_kg: string;
  shoulder_height_cm: string;
  service_role: string;
}

export function emptyPetDraft(): PetDraft {
  return {
    display_name: "",
    species: "dog",
    breed_text: "",
    weight_kg: "",
    shoulder_height_cm: "",
    service_role: "none",
  };
}
