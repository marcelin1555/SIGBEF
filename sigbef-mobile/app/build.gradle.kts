plugins {
  alias(libs.plugins.android.application)
  alias(libs.plugins.kotlin.compose)
  alias(libs.plugins.google.devtools.ksp)
}

android {
  namespace = "br.rn.cefe.sigbef"
  compileSdk { version = release(36) { minorApiLevel = 1 } }

  defaultConfig {
    applicationId = "br.rn.cefe.sigbef"
    minSdk = 24
    targetSdk = 36
    versionCode = 2
    versionName = "0.2"

    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
  }

  signingConfigs {
    // Só cria a config de release se a chave existir de fato. Assim
    // `assembleRelease` funciona para quem clona o repositório (gera APK
    // não assinado); a assinatura real acontece na publicação, quando a
    // chave e as senhas são fornecidas por variável de ambiente. Antes
    // isto era obrigatório e apontava para um my-upload-key.jks ausente,
    // quebrando o build de release.
    val keystorePath = System.getenv("KEYSTORE_PATH") ?: "${rootDir}/my-upload-key.jks"
    if (file(keystorePath).exists()) {
      val senhaStore = System.getenv("STORE_PASSWORD")
      val senhaChave = System.getenv("KEY_PASSWORD")
      if (senhaStore.isNullOrBlank() || senhaChave.isNullOrBlank()) {
        // Falha cedo e explicando. Sem isto, o build seguia e só quebrava
        // lá na frente com um erro do Gradle que não diz o que fazer.
        throw GradleException(
          "A chave de assinatura foi encontrada em $keystorePath, mas as " +
            "senhas não estão no ambiente. Defina STORE_PASSWORD e " +
            "KEY_PASSWORD antes de rodar o build. Ver docs/COMO_GERAR_APK.md."
        )
      }
      create("release") {
        storeFile = file(keystorePath)
        storePassword = senhaStore
        keyAlias = System.getenv("KEY_ALIAS") ?: "upload"
        keyPassword = senhaChave
      }
    }
  }

  buildTypes {
    release {
      isCrunchPngs = false
      isMinifyEnabled = false
      proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
      // null quando não há chave: build sai sem assinatura, sem falhar.
      signingConfig = signingConfigs.findByName("release")
    }
    // debug usa a chave de depuração padrão do Android SDK; a config
    // antiga apontava para um debug.keystore que nao esta no repositorio
    // (e nem deve estar), quebrando o build de quem clonasse o projeto.
    debug { }
  }

  /*
   * Um APK por arquitetura, no release.
   *
   * O leitor de QR traz um motor nativo (libbarhopper) de ~5 MB para
   * CADA arquitetura. Num APK único isso são ~20 MB que o aluno baixa
   * sem usar: o celular roda só a dele. Separando, o arquivo que ele
   * instala volta ao tamanho de antes.
   *
   * O universalApk continua sendo gerado para quando é preciso um
   * arquivo só — passar o app por cabo ou por WhatsApp na escola, sem
   * saber de antemão qual é o aparelho.
   */
  splits {
    abi {
      isEnable = true
      reset()
      include("armeabi-v7a", "arm64-v8a", "x86", "x86_64")
      isUniversalApk = true
    }
  }
  compileOptions {
    sourceCompatibility = JavaVersion.VERSION_11
    targetCompatibility = JavaVersion.VERSION_11
  }
  buildFeatures {
    compose = true
    buildConfig = true
  }
  testOptions { unitTests { isIncludeAndroidResources = true } }
}

dependencies {
  implementation(platform(libs.androidx.compose.bom))
  // implementation(libs.accompanist.permissions)
  implementation(libs.androidx.activity.compose)
  implementation(libs.androidx.camera.camera2)
  implementation(libs.androidx.camera.core)
  implementation(libs.androidx.camera.lifecycle)
  implementation(libs.androidx.camera.view)
  implementation(libs.mlkit.barcode.scanning)
  implementation(libs.androidx.compose.material.icons.core)
  implementation(libs.androidx.compose.material.icons.extended)
  implementation(libs.androidx.compose.material3)
  implementation(libs.androidx.compose.ui)
  implementation(libs.androidx.compose.ui.graphics)
  implementation(libs.androidx.compose.ui.tooling.preview)
  implementation(libs.androidx.core.ktx)
  // implementation(libs.androidx.datastore.preferences)
  implementation(libs.androidx.lifecycle.runtime.compose)
  implementation(libs.androidx.lifecycle.runtime.ktx)
  implementation(libs.androidx.lifecycle.viewmodel.compose)
  // implementation(libs.androidx.navigation.compose)
  implementation(libs.androidx.work.runtime)
  implementation(libs.androidx.room.ktx)
  implementation(libs.androidx.room.runtime)
  // implementation(libs.coil.compose)
  implementation(libs.converter.moshi)
  // implementation(libs.androidx.credentials)
  // implementation(libs.androidx.credentials.play.services)
  // implementation(libs.googleid)
  implementation(libs.kotlinx.coroutines.android)
  implementation(libs.kotlinx.coroutines.core)
  implementation(libs.logging.interceptor)
  implementation(libs.moshi.kotlin)
  implementation(libs.okhttp)
  // implementation(libs.play.services.location)
  implementation(libs.retrofit)
  testImplementation(libs.androidx.compose.ui.test.junit4)
  testImplementation(libs.androidx.core)
  testImplementation(libs.androidx.junit)
  testImplementation(libs.junit)
  testImplementation(libs.kotlinx.coroutines.test)
  testImplementation(libs.robolectric)
  androidTestImplementation(platform(libs.androidx.compose.bom))
  androidTestImplementation(libs.androidx.compose.ui.test.junit4)
  androidTestImplementation(libs.androidx.espresso.core)
  androidTestImplementation(libs.androidx.junit)
  androidTestImplementation(libs.androidx.runner)
  debugImplementation(libs.androidx.compose.ui.test.manifest)
  debugImplementation(libs.androidx.compose.ui.tooling)
  "ksp"(libs.androidx.room.compiler)
  "ksp"(libs.moshi.kotlin.codegen)
}
