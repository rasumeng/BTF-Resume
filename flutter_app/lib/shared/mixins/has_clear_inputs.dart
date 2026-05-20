/// Mixin for screens that can clear their input fields on tab switch
/// Used to preserve results while clearing input fields when switching tabs
mixin HasClearInputs {
  /// Clear input fields while preserving results
  /// Call this when switching away from this tab
  void clearInputFields();
}