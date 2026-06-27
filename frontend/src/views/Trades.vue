<template>
  <div><h2>{{ title }}</h2><div class="panel"><p>Loading data from API...</p></div></div>
</template>
<script>
export default { props: ['trades','riskEvents','modelStatus','systemHealth'], computed: { title() { return this.$route.name } } }
</script>
<style scoped>.panel { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }</style>
