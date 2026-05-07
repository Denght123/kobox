<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <footer class="footer-wrap">
    <div class="footer-links">
      <a href="mailto:3403666426@qq.com">{{ t('footer.contact') }} 3403666426@qq.com</a>
      <a href="#">{{ t('footer.terms') }}</a>
      <a href="#">{{ t('footer.privacy') }}</a>
    </div>
    <p class="copyright">{{ t('footer.copyright') }}</p>
  </footer>
</template>

<style scoped>
.footer-wrap {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
  justify-content: center;
  padding: 18px 0 10px;
}

.copyright {
  margin: 0;
  color: #d58ea0;
  font-family: "Plus Jakarta Sans", sans-serif;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-size: 10px;
}
</style>
