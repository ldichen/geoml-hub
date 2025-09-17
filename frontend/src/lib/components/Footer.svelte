<script>
  import { _ } from 'svelte-i18n';
  import { Github, Mail, ExternalLink } from 'lucide-svelte';
</script>

<footer class="bg-gray-900 border-t border-gray-700 mt-16">
  <div class="container">
    <div class="py-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
        <!-- About -->
        <div class="col-span-1 md:col-span-2">
          <div class="flex items-center space-x-3 mb-4">
            <img src="/logo.png" alt="GeoML Hub" class="h-12 object-contain" />
            <div>
              <h3 class="text-lg font-semibold text-white">
                {$_('app.name')}
              </h3>
              <p class="text-gray-300">
                {$_('app.description')}
              </p>
            </div>
          </div>

          <p class="text-sm text-gray-400">
            地理科学领域设计的机器学习模型库，汇聚全球地理学者的智慧，推动地理科学与人工智能的融合发展。
          </p>
        </div>
        
        <!-- Quick Links -->
        <div>
          <h4 class="text-sm font-semibold text-white uppercase tracking-wide mb-4">
            快速导航
          </h4>
          <ul class="space-y-2">
            <li>
              <a href="http://geomodeling.njnu.edu.cn/" class="text-gray-300 hover:text-primary-300 transition-colors">
                {$_('openGMS.openGMS')}
              </a>
            </li>
          </ul>
        </div>
        
        <!-- Contact & Support -->
        <div>
          <h4 class="text-sm font-semibold text-white uppercase tracking-wide mb-4">
            联系我们
          </h4>
          <ul class="space-y-2">
            <li>
              <a href="mailto:opengms@njnu.edu.cn" class="flex items-center space-x-2 text-gray-300 hover:text-primary-300 transition-colors">
                <Mail class="w-4 h-4" />
                <span>opengms@njnu.edu.cn</span>
              </a>
            </li>
          </ul>
        </div>
      </div>
      
      <div class="border-t border-gray-700 mt-6 pt-6 flex flex-col sm:flex-row justify-center items-center">
        <p class="text-sm text-gray-400">
          Copyright © 2011-2023 OpenGMS. All Rights Reserved.
        </p>
      </div>
    </div>
  </div>
</footer>