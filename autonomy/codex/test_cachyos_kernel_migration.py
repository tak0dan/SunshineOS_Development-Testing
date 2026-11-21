import unittest

from autonomy.codex.cachyos_kernel_migration import review_kernel_transition


class CachyKernelMigrationTests(unittest.TestCase):
    def test_CKM_001_cachy_variant_requires_explicit_target(self):
        result = review_kernel_transition(["linux-cachyos", "linux-firmware"])
        self.assertFalse(result.ready)
        self.assertIn("CACHY_KERNEL_MAPPING_REQUIRED: CachyOS kernel variants require an explicit target mapping", result.blockers)

    def test_CKM_002_target_without_fallback_blocks_source_retirement(self):
        result = review_kernel_transition(["linux-cachyos"], target_kernels=["linux"])
        self.assertIn("KERNEL_FALLBACK_REQUIRED: keep an installed source kernel or identify an installed fallback", result.blockers)

    def test_CKM_003_existing_fallback_and_mapped_target_are_reviewable(self):
        result = review_kernel_transition(
            ["linux-cachyos", "linux-lts"],
            target_kernels=["linux"],
            fallback_kernels=["linux-lts"],
            active_kernel_package="linux-lts",
        )
        self.assertTrue(result.ready)
        self.assertEqual(result.retained_kernels, ("linux-lts",))
        self.assertTrue(any("does not authorize package removal" in d for d in result.decisions))

    def test_CKM_004_active_kernel_cannot_be_removed_without_boot_validation(self):
        result = review_kernel_transition(
            ["linux-cachyos", "linux-lts"],
            target_kernels=["linux"],
            fallback_kernels=["linux-lts"],
            active_kernel_package="linux-cachyos",
        )
        # The fallback permits planning, but active-kernel retirement remains blocked.
        self.assertIn("ACTIVE_KERNEL_RETIREMENT_BLOCKED: active kernel cannot be retired before target boot validation", result.blockers)

    def test_CKM_005_non_cachy_kernel_is_preserved_without_replacement(self):
        result = review_kernel_transition(["linux-lts"], active_kernel_package="linux-lts")
        self.assertTrue(result.ready)
        self.assertEqual(result.retained_kernels, ("linux-lts",))

    def test_CKM_006_blank_target_identity_fails_closed(self):
        result = review_kernel_transition(["linux-cachyos"], target_kernels=[""])
        self.assertIn("KERNEL_TARGET_INVALID: target kernel identities are invalid", result.blockers)


if __name__ == "__main__":
    unittest.main()
