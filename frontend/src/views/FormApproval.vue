<template>
  <div class="form-approval-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon :size="22" color="#3b82f6"><DocumentChecked /></el-icon>
          表单审批中心
        </h2>
        <p class="page-subtitle">施工进度计划、变更申请、异常报告等各类业务表单的统一审批管理</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tab-bar">
      <div
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-item"
        :class="{ active: activeTab === tab.key }"
        @click="handleTabChange(tab.key)"
      >
        <span class="tab-label">{{ tab.label }}</span>
        <el-tag v-if="tabBadge(tab.key) > 0" size="small" round :type="tab.badgeType || 'info'" effect="dark">
          {{ tabBadge(tab.key) }}
        </el-tag>
      </div>
    </div>

    <!-- 筛选区 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-select
          v-model="filters.formType"
          placeholder="表单类型"
          clearable
          class="filter-select"
        >
          <el-option
            v-for="ft in formTypes"
            :key="ft.key || ft.value"
            :label="ft.label || ft.name"
            :value="ft.key || ft.value"
          />
        </el-select>

        <el-select
          v-model="filters.projectId"
          placeholder="所属项目"
          clearable
          class="filter-select"
        >
          <el-option
            v-for="p in projects"
            :key="p.id"
            :label="p.name"
            :value="p.id"
          />
        </el-select>

        <el-input
          v-model="filters.keyword"
          placeholder="搜索标题、创建人..."
          clearable
          class="filter-input"
          :prefix-icon="Search"
          @keyup.enter="loadForms"
        />

        <el-button type="primary" @click="loadForms">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button @click="resetFilters">
          <el-icon><RefreshLeft /></el-icon>
          重置
        </el-button>
      </div>
      <div class="filter-right">
        <el-button type="success" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          新建表单
        </el-button>
      </div>
    </div>

    <!-- 统计条 -->
    <div class="stats-bar">
      <div v-for="(s, idx) in statsCards" :key="idx" class="stats-mini-card" :class="s.colorClass">
        <div class="stats-icon"><el-icon :size="20"><component :is="s.icon" /></el-icon></div>
        <div class="stats-body">
          <div class="stats-value">{{ s.value }}</div>
          <div class="stats-label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="table-card">
      <el-table
        v-loading="tableLoading"
        :data="tableData"
        stripe
        style="width: 100%"
        empty-text="暂无表单数据"
        :header-cell-style="{ background: '#f8fafc', color: '#334155', fontWeight: 600 }"
      >
        <el-table-column prop="title" label="标题" min-width="240">
          <template #default="{ row }">
            <div class="col-title">
              <el-icon color="#3b82f6"><Document /></el-icon>
              <span class="title-text" @click="openDetail(row)">{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="formType" label="类型" width="140">
          <template #default="{ row }">
            <el-tag :type="typeTagType(row.form_type)" effect="light" round size="small">
              {{ getTypeLabel(row.form_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="light" round size="small">
              <el-icon><component :is="statusIcon(row.status)" /></el-icon>
              &nbsp;{{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="projectName" label="所属项目" width="180">
          <template #default="{ row }">
            <span class="col-project">
              <el-icon color="#6366f1"><FolderOpened /></el-icon>
              {{ row.project_name || '-' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="creator" label="创建人" width="110">
          <template #default="{ row }">
            <div class="col-user">
              <el-avatar :size="24" class="user-avatar">{{ (row.creator_name || row.creator || 'U').slice(0,1) }}</el-avatar>
              <span>{{ row.creator_name || row.creator || '-' }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="createdAt" label="创建时间" width="160">
          <template #default="{ row }">
            <span class="col-time">{{ formatDate(row.created_at || row.createdAt) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="currentStep" label="当前步骤" width="140">
          <template #default="{ row }">
            <el-tooltip v-if="row.approval_chain && row.approval_chain.length" :content="approvalChainText(row)" placement="top">
              <div class="col-step">
                <el-steps :active="currentStepIndex(row)" :process-status="stepProcessStatus(row)" size="mini" finish-status="success">
                  <el-step v-for="(_, i) in row.approval_chain.slice(0,3)" :key="i" />
                </el-steps>
                <span class="step-label">{{ currentStepText(row) }}</span>
              </div>
            </el-tooltip>
            <span v-else class="col-step-simple">{{ row.current_step || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDetail(row)">
              <el-icon><View /></el-icon>查看
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              type="success" link size="small"
              @click="handleSubmit(row)"
            >
              <el-icon><Promotion /></el-icon>提交
            </el-button>
            <el-button
              v-if="row.status === 'pending' && canApprove(row)"
              type="warning" link size="small"
              @click="openDetail(row, true)"
            >
              <el-icon><Check /></el-icon>审批
            </el-button>
            <el-popconfirm
              v-if="row.status === 'draft'"
              title="确定删除该草稿表单吗？"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" link size="small">
                  <el-icon><Delete /></el-icon>删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="loadForms"
          @current-change="loadForms"
        />
      </div>
    </div>

    <!-- 新建表单对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建业务表单"
      width="680px"
      :close-on-click-modal="false"
      class="create-form-dialog"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="110px"
        label-position="right"
      >
        <el-form-item label="表单类型" prop="form_type">
          <el-select v-model="createForm.form_type" placeholder="请选择表单类型" style="width: 100%" @change="onTypeChange">
            <el-option
              v-for="ft in formTypes"
              :key="ft.key || ft.value"
              :label="ft.label || ft.name"
              :value="ft.key || ft.value"
            >
              <span style="float:left">{{ ft.label || ft.name }}</span>
              <span style="float:right;color:#94a3b8;font-size:12px">{{ ft.description || '' }}</span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="所属项目" prop="project_id">
          <el-select v-model="createForm.project_id" placeholder="请选择所属项目" style="width: 100%" filterable>
            <el-option
              v-for="p in projects"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="表单标题" prop="title">
          <el-input v-model="createForm.title" placeholder="请输入表单标题" maxlength="100" show-word-limit />
        </el-form-item>

        <!-- 动态表单区域 -->
        <div v-if="createForm.form_type" class="dynamic-form-section">
          <el-divider content-position="left">
            <span class="divider-title">
              <el-icon color="#3b82f6"><Edit /></el-icon>
              {{ getTypeLabel(createForm.form_type) }} - 业务字段
            </span>
          </el-divider>

          <!-- schedule_plan 施工进度计划 -->
          <template v-if="createForm.form_type === 'schedule_plan'">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="开挖量 (m³)" prop="data.excavation">
                  <el-input-number v-model="createForm.data.excavation" :min="0" :step="1000" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="回填量 (m³)" prop="data.backfill">
                  <el-input-number v-model="createForm.data.backfill" :min="0" :step="1000" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="借方量 (m³)" prop="data.borrow">
                  <el-input-number v-model="createForm.data.borrow" :min="0" :step="1000" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="弃方量 (m³)" prop="data.waste">
                  <el-input-number v-model="createForm.data.waste" :min="0" :step="1000" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="施工周期" prop="data.period">
                  <el-date-picker
                    v-model="createForm.data.period"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="弃渣场" prop="data.waste_sites">
                  <el-select
                    v-model="createForm.data.waste_sites"
                    multiple
                    filterable
                    placeholder="请选择弃渣场"
                    style="width: 100%"
                  >
                    <el-option label="1号弃渣场 (东沟)" value="ws_01" />
                    <el-option label="2号弃渣场 (西沟)" value="ws_02" />
                    <el-option label="3号弃渣场 (南坡)" value="ws_03" />
                    <el-option label="临时中转场" value="ws_temp" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </template>

          <!-- change_request 变更申请 -->
          <template v-else-if="createForm.form_type === 'change_request'">
            <el-form-item label="变更位置" prop="data.location">
              <el-input v-model="createForm.data.location" placeholder="如：EL580~EL620 段坝肩左岸" />
            </el-form-item>
            <el-form-item label="原设计" prop="data.original_design">
              <el-input v-model="createForm.data.original_design" type="textarea" :rows="2" placeholder="描述原设计方案" />
            </el-form-item>
            <el-form-item label="建议设计" prop="data.proposed_design">
              <el-input v-model="createForm.data.proposed_design" type="textarea" :rows="2" placeholder="描述变更后建议方案" />
            </el-form-item>
            <el-form-item label="变更理由" prop="data.reason">
              <el-input v-model="createForm.data.reason" type="textarea" :rows="3" placeholder="详细说明变更原因及依据" />
            </el-form-item>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="成本增加 (%)" prop="data.cost_increase_pct">
                  <el-input-number v-model="createForm.data.cost_increase_pct" :min="0" :max="100" :precision="2" :step="0.5" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="工期延误 (天)" prop="data.delay_days">
                  <el-input-number v-model="createForm.data.delay_days" :min="0" :step="1" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
          </template>

          <!-- exception_report 异常报告 -->
          <template v-else-if="createForm.form_type === 'exception_report'">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="传感器编号" prop="data.sensor_code">
                  <el-input v-model="createForm.data.sensor_code" placeholder="如：S-017" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="监测周期" prop="data.period">
                  <el-date-picker
                    v-model="createForm.data.period"
                    type="daterange"
                    range-separator="至"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="平均速率 (mm/h)" prop="data.avg_rate">
                  <el-input-number v-model="createForm.data.avg_rate" :precision="3" :step="0.01" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="阈值 (mm/h)" prop="data.threshold">
                  <el-input-number v-model="createForm.data.threshold" :precision="3" :step="0.1" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="异常分析" prop="data.analysis">
              <el-input v-model="createForm.data.analysis" type="textarea" :rows="4" placeholder="详细分析异常原因、影响范围及建议处理措施" />
            </el-form-item>
          </template>

          <!-- geology_survey 地质勘察报告 -->
          <template v-else-if="createForm.form_type === 'geology_survey'">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="勘察区域" prop="data.area">
                  <el-input v-model="createForm.data.area" placeholder="如：左岸 EL520-EL600" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="钻孔数量" prop="data.borehole_count">
                  <el-input-number v-model="createForm.data.borehole_count" :min="1" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="最大孔深 (m)" prop="data.max_depth">
                  <el-input-number v-model="createForm.data.max_depth" :min="0" :precision="1" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="地层数" prop="data.layer_count">
                  <el-input-number v-model="createForm.data.layer_count" :min="1" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="地质结论" prop="data.conclusion">
              <el-input v-model="createForm.data.conclusion" type="textarea" :rows="3" placeholder="主要地质结论与建议" />
            </el-form-item>
          </template>

          <!-- monitoring_report 监测报告 -->
          <template v-else-if="createForm.form_type === 'monitoring_report'">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="报告周期" prop="data.period_type">
                  <el-select v-model="createForm.data.period_type" style="width: 100%">
                    <el-option label="日报" value="daily" />
                    <el-option label="周报" value="weekly" />
                    <el-option label="月报" value="monthly" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="监测点数量" prop="data.point_count">
                  <el-input-number v-model="createForm.data.point_count" :min="1" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="最大位移 (mm)" prop="data.max_displacement">
                  <el-input-number v-model="createForm.data.max_displacement" :precision="2" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="最大应力 (MPa)" prop="data.max_stress">
                  <el-input-number v-model="createForm.data.max_stress" :precision="3" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="监测结论" prop="data.conclusion">
              <el-input v-model="createForm.data.conclusion" type="textarea" :rows="3" placeholder="本期监测结论、预警情况及建议" />
            </el-form-item>
          </template>

          <!-- param_calculation 参数计算书 -->
          <template v-else-if="createForm.form_type === 'param_calculation'">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="计算工况" prop="data.stage">
                  <el-input v-model="createForm.data.stage" placeholder="如：工况15 / 开挖第5步" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="计算方法" prop="data.method">
                  <el-select v-model="createForm.data.method" style="width: 100%">
                    <el-option label="有限元法 (FEM)" value="fem" />
                    <el-option label="极限平衡法" value="limit_eq" />
                    <el-option label="反演分析法" value="inversion" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="凝聚力 c (kPa)" prop="data.cohesion">
                  <el-input-number v-model="createForm.data.cohesion" :precision="2" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="内摩擦角 φ (°)" prop="data.friction_angle">
                  <el-input-number v-model="createForm.data.friction_angle" :precision="2" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="弹性模量 E (GPa)" prop="data.elastic_modulus">
                  <el-input-number v-model="createForm.data.elastic_modulus" :precision="3" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="计算结果说明" prop="data.result">
              <el-input v-model="createForm.data.result" type="textarea" :rows="3" placeholder="安全系数、关键位移等计算结果" />
            </el-form-item>
          </template>

          <!-- earthwork_allocation 土石方调配 -->
          <template v-else-if="createForm.form_type === 'earthwork_allocation'">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="调配周期" prop="data.period">
                  <el-date-picker v-model="createForm.data.period" type="daterange" range-separator="至" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="调配方量 (万m³)" prop="data.total_volume">
                  <el-input-number v-model="createForm.data.total_volume" :min="0" :precision="2" :step="0.5" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="平均运距 (km)" prop="data.avg_distance">
                  <el-input-number v-model="createForm.data.avg_distance" :min="0" :precision="2" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="运输设备" prop="data.equipment">
                  <el-select v-model="createForm.data.equipment" style="width: 100%">
                    <el-option label="自卸车 (20t)" value="truck_20t" />
                    <el-option label="自卸车 (30t)" value="truck_30t" />
                    <el-option label="皮带机运输" value="belt" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="调配效率" prop="data.efficiency_pct">
                  <el-input-number v-model="createForm.data.efficiency_pct" :min="0" :max="100" :precision="1" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="调配方案说明" prop="data.description">
              <el-input v-model="createForm.data.description" type="textarea" :rows="3" placeholder="取土区、填筑区、运输路径等关键说明" />
            </el-form-item>
          </template>

          <el-empty v-else description="该表单类型暂无自定义字段" :image-size="80" />
        </div>
      </el-form>

      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button @click="handleSaveDraft">
          <el-icon><DocumentAdd /></el-icon>保存草稿
        </el-button>
        <el-button type="primary" @click="handleCreateSubmit">
          <el-icon><Promotion /></el-icon>保存并提交
        </el-button>
      </template>
    </el-dialog>

    <!-- 表单详情抽屉 -->
    <el-drawer
      v-model="detailVisible"
      :title="detailDrawerTitle"
      direction="rtl"
      size="640px"
      :before-close="beforeCloseDetail"
    >
      <template v-if="currentDetail">
        <!-- 审批链步骤条 -->
        <div v-if="currentDetail.approval_chain && currentDetail.approval_chain.length" class="approval-chain">
          <div class="chain-title">
            <el-icon color="#3b82f6"><Connection /></el-icon>
            审批流程
          </div>
          <el-steps
            :active="currentStepIndex(currentDetail)"
            :process-status="stepProcessStatus(currentDetail)"
            finish-status="success"
            direction="vertical"
          >
            <el-step
              v-for="(step, idx) in currentDetail.approval_chain"
              :key="idx"
              :title="step.role || step.name || `审批节点 ${idx+1}`"
              :description="stepDescription(step)"
              :status="stepStatus(step)"
              :icon="stepIcon(step)"
            />
          </el-steps>
        </div>

        <!-- 基本信息 -->
        <el-divider content-position="left">
          <span class="divider-title">
            <el-icon color="#3b82f6"><InfoFilled /></el-icon>
            基本信息
          </span>
        </el-divider>
        <el-descriptions :column="2" border size="default" class="desc-info">
          <el-descriptions-item label="表单标题" :span="2">{{ currentDetail.title }}</el-descriptions-item>
          <el-descriptions-item label="表单类型">
            <el-tag :type="typeTagType(currentDetail.form_type)" effect="light" round>
              {{ getTypeLabel(currentDetail.form_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="statusTagType(currentDetail.status)" effect="light" round>
              {{ statusLabel(currentDetail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="所属项目">{{ currentDetail.project_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="表单编号">{{ currentDetail.form_no || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建人">{{ currentDetail.creator_name || currentDetail.creator || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(currentDetail.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="提交时间" :span="2">{{ formatDate(currentDetail.submitted_at) || '-' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 业务字段（从 data JSON 渲染） -->
        <el-divider content-position="left">
          <span class="divider-title">
            <el-icon color="#3b82f6"><DataLine /></el-icon>
            业务数据
          </span>
        </el-divider>
        <el-descriptions :column="2" border size="default" class="desc-data">
          <template v-for="(item, idx) in detailDataFields" :key="idx">
            <el-descriptions-item :label="item.label" :span="item.full ? 2 : 1">
              <template v-if="item.isDateRange && Array.isArray(item.value)">
                {{ item.value[0] }} ~ {{ item.value[1] }}
              </template>
              <template v-else-if="Array.isArray(item.value) && item.value.length">
                <el-tag v-for="(v, vi) in item.value" :key="vi" size="small" effect="plain" style="margin-right:4px">{{ v }}</el-tag>
              </template>
              <template v-else-if="item.value !== null && item.value !== undefined && item.value !== ''">
                {{ item.value }}{{ item.unit || '' }}
              </template>
              <span v-else class="empty-val">-</span>
            </el-descriptions-item>
          </template>
          <el-descriptions-item v-if="detailDataFields.length === 0" label="暂无数据" :span="2">-</el-descriptions-item>
        </el-descriptions>

        <!-- 审批历史 -->
        <el-divider v-if="currentDetail.approval_history && currentDetail.approval_history.length" content-position="left">
          <span class="divider-title">
            <el-icon color="#3b82f6"><Clock /></el-icon>
            审批记录
          </span>
        </el-divider>
        <div v-if="currentDetail.approval_history && currentDetail.approval_history.length" class="approval-history">
          <el-timeline>
            <el-timeline-item
              v-for="(h, idx) in currentDetail.approval_history"
              :key="idx"
              :timestamp="formatDate(h.time || h.created_at)"
              :type="h.action === 'approve' ? 'success' : h.action === 'reject' ? 'danger' : 'primary'"
              size="large"
            >
              <div class="history-item">
                <div class="history-title">
                  <b>{{ h.user_name || h.user }}</b>
                  <el-tag :type="h.action === 'approve' ? 'success' : h.action === 'reject' ? 'danger' : 'info'" size="small" effect="light">
                    {{ h.action === 'approve' ? '审批通过' : h.action === 'reject' ? '审批驳回' : '提交' }}
                  </el-tag>
                </div>
                <div v-if="h.comment" class="history-comment">意见：{{ h.comment }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>

        <!-- 底部审批操作 -->
        <div v-if="showApprovalActions" class="approval-actions">
          <el-divider />
          <div class="actions-form">
            <el-form :model="approvalForm" label-width="80px">
              <el-form-item label="审批意见">
                <el-input
                  v-model="approvalForm.comment"
                  type="textarea"
                  :rows="3"
                  :placeholder="approvalForm.action === 'approve' ? '请输入通过意见（可选）' : '请输入驳回理由（必填）'"
                />
              </el-form-item>
              <div class="actions-btns">
                <el-button @click="showApprovalActions = false">取消</el-button>
                <el-button type="danger" :loading="approvalLoading" @click="handleApprove('reject')">
                  <el-icon><Close /></el-icon>驳回
                </el-button>
                <el-button type="success" :loading="approvalLoading" @click="handleApprove('approve')">
                  <el-icon><Check /></el-icon>通过
                </el-button>
              </div>
            </el-form>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, RefreshLeft, Plus, Document, FolderOpened, View, Promotion, Check, Delete,
  Edit, InfoFilled, DataLine, Clock, Connection, Close, DocumentAdd,
} from '@element-plus/icons-vue'
import * as api from '@/api'
import { useUserStore } from '@/stores/user'

// ========== 通用解包函数：兼容后端返回 {items/data/list} 或裸 list/object ==========
function unwrapList(r, fallback = []) {
  if (Array.isArray(r)) return r
  if (!r || typeof r !== 'object') return fallback
  if (Array.isArray(r.items)) return r.items
  if (Array.isArray(r.list)) return r.list
  if (Array.isArray(r.data)) return r.data
  if (r.data && typeof r.data === 'object') {
    if (Array.isArray(r.data.items)) return r.data.items
    if (Array.isArray(r.data.list)) return r.data.list
    if (Array.isArray(r.data.data)) return r.data.data
  }
  return fallback
}
function unwrapObject(r, fallback = {}) {
  if (r && typeof r === 'object' && !Array.isArray(r)) return r
  if (!r) return fallback
  if (r.data && typeof r.data === 'object' && !Array.isArray(r.data)) return r.data
  if (r.items && typeof r.items === 'object' && !Array.isArray(r.items)) return r.items
  if (r.list && typeof r.list === 'object' && !Array.isArray(r.list)) return r.list
  return fallback
}

const route = useRoute()
const userStore = useUserStore()

// ========== Tabs ==========
const tabs = [
  { key: 'all', label: '全部', badgeType: 'info' },
  { key: 'pending', label: '我待办', badgeType: 'warning' },
  { key: 'draft', label: '草稿', badgeType: 'info' },
  { key: 'approving', label: '审批中', badgeType: 'primary' },
  { key: 'approved', label: '已通过', badgeType: 'success' },
  { key: 'rejected', label: '已驳回', badgeType: 'danger' },
]
const activeTab = ref('all')
function handleTabChange(k) {
  activeTab.value = k
  pagination.page = 1
  loadForms()
}

// ========== 路由参数同步 ==========
onMounted(() => {
  if (route.query.tab && tabs.find(t => t.key === route.query.tab)) {
    activeTab.value = route.query.tab
  }
})

// ========== 数据：表单类型、项目 ==========
const formTypes = ref([])
const projects = ref([])

const typeMeta = {
  schedule_plan: { label: '施工进度计划', tagType: 'primary', desc: '施工进度与土石方调配计划' },
  change_request: { label: '变更申请', tagType: 'warning', desc: '设计与方案变更申请' },
  exception_report: { label: '异常报告', tagType: 'danger', desc: '监测异常与突发事件报告' },
  geology_survey: { label: '地质勘察报告', tagType: 'success', desc: '地质勘察与钻孔成果报告' },
  monitoring_report: { label: '监测报告', tagType: 'info', desc: '周期监测数据分析报告' },
  param_calculation: { label: '参数计算书', tagType: 'purple', desc: '岩土参数反演与计算' },
  earthwork_allocation: { label: '土石方调配', tagType: '', desc: '土石方平衡调配方案' },
}

function getTypeLabel(t) { return typeMeta[t]?.label || t }
function typeTagType(t) {
  const m = typeMeta[t]?.tagType
  return ['primary','success','warning','danger','info'].includes(m) ? m : ''
}

// ========== 筛选 ==========
const filters = reactive({
  formType: '',
  projectId: '',
  keyword: '',
})
function resetFilters() {
  filters.formType = ''
  filters.projectId = ''
  filters.keyword = ''
  loadForms()
}

// ========== 统计 ==========
const stats = reactive({ total: 0, my_pending: 0, approved: 0, rejected: 0 })
const statsCards = computed(() => [
  { label: '表单总数', value: stats.total, icon: 'DocumentCopy', colorClass: 'sm-blue' },
  { label: '我的待办', value: stats.my_pending, icon: 'Message', colorClass: 'sm-orange' },
  { label: '已通过', value: stats.approved, icon: 'CircleCheck', colorClass: 'sm-green' },
  { label: '已驳回', value: stats.rejected, icon: 'CircleClose', colorClass: 'sm-red' },
])
function tabBadge(key) {
  switch (key) {
    case 'pending': return stats.my_pending
    case 'draft': return stats.draft || 0
    case 'approving': return stats.approving || 0
    case 'approved': return stats.approved
    case 'rejected': return stats.rejected
    default: return 0
  }
}

// ========== 表格 ==========
const tableLoading = ref(false)
const tableData = ref([])
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

const statusMeta = {
  draft: { label: '草稿', type: 'info', icon: 'EditPen' },
  pending: { label: '待审批', type: 'warning', icon: 'Clock' },
  approving: { label: '审批中', type: 'primary', icon: 'Loading' },
  approved: { label: '已通过', type: 'success', icon: 'CircleCheck' },
  rejected: { label: '已驳回', type: 'danger', icon: 'CircleClose' },
}
function statusLabel(s) { return statusMeta[s]?.label || s }
function statusTagType(s) { return statusMeta[s]?.type || 'info' }
function statusIcon(s) { return statusMeta[s]?.icon || 'Document' }

function formatDate(d) {
  if (!d) return ''
  const dt = new Date(d)
  if (isNaN(dt.getTime())) return d
  const pad = (n) => String(n).padStart(2, '0')
  return `${dt.getFullYear()}-${pad(dt.getMonth()+1)}-${pad(dt.getDate())} ${pad(dt.getHours())}:${pad(dt.getMinutes())}`
}

function approvalChainText(row) {
  return (row.approval_chain || []).map(s => `${s.role || s.name || '节点'} (${s.status || '待审'})`).join(' → ')
}
function currentStepIndex(row) {
  const chain = row.approval_chain || []
  if (row.status === 'draft' || row.status === 'pending') return 0
  if (row.status === 'approved') return chain.length
  if (row.status === 'rejected') {
    const idx = chain.findIndex(s => s.status === 'rejected')
    return idx >= 0 ? idx + 1 : 0
  }
  const idx = chain.findIndex(s => s.status === 'pending' || s.status === 'current')
  return idx >= 0 ? idx : chain.findIndex(s => !s.status)
}
function currentStepText(row) {
  const chain = row.approval_chain || []
  const idx = currentStepIndex(row)
  if (row.status === 'draft') return '草稿'
  if (row.status === 'approved') return '已完成'
  if (row.status === 'rejected') return '已驳回'
  if (idx < chain.length) return chain[idx].role || chain[idx].name || `步骤${idx+1}`
  return '-'
}
function stepProcessStatus(row) {
  if (row.status === 'rejected') return 'error'
  return row.status === 'approved' ? 'success' : 'process'
}
function canApprove(row) {
  // 简化：只要 pending 状态，且非创建者，即可审批
  if (row.status !== 'pending') return false
  return row.creator !== userStore.username
}

// ========== 加载 ==========
async function loadFormTypes() {
  try {
    const r = await api.getFormTypes()
    const raw = unwrapList(r, [])
    // 后端 [{type, label, approval_chain} -> 前端 {key, label, description}
    if (raw.length) {
      formTypes.value = raw.map(x => ({
        key: x.key || x.value || x.type,
        label: x.label || x.name || x.type,
        description: x.description || typeMeta[x.key || x.value || x.type]?.desc || '',
        approval_chain: x.approval_chain || [],
      }))
    } else {
      formTypes.value = Object.entries(typeMeta).map(([k, v]) => ({
        key: k, label: v.label, description: v.desc,
      }))
    }
  } catch {
    formTypes.value = Object.entries(typeMeta).map(([k, v]) => ({
      key: k, label: v.label, description: v.desc,
    }))
  }
}

async function loadProjects() {
  try {
    const r = await api.listProjects({ page_size: 100 })
    projects.value = unwrapList(r, [])
  } catch {
    projects.value = [
      { id: 'P001', name: '古贤枢纽左岸边坡开挖' },
      { id: 'P002', name: '右岸坝肩开挖工程' },
      { id: 'P003', name: '导流洞工程' },
      { id: 'P004', name: '溢洪道工程' },
    ]
  }
}

async function loadStats() {
  try {
    const r = await api.getFormStats()
    const raw = unwrapObject(r, {})
    Object.assign(stats, {
      total: raw.total ?? 0,
      my_pending: raw.my_pending ?? 0,
      approved: raw.approved ?? 0,
      rejected: raw.rejected ?? 0,
      draft: raw.draft ?? 0,
      approving: raw.approving ?? raw.pending ?? 0,
    })
  } catch {
    Object.assign(stats, { total: 73, my_pending: 8, approved: 52, rejected: 6, draft: 5, approving: 10 })
  }
}

async function loadForms() {
  tableLoading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      form_type: filters.formType || undefined,
      project_id: filters.projectId || undefined,
    }
    if (activeTab.value !== 'all') params.status_filter = activeTab.value
    const r = await api.listForms(params)
    const raw = unwrapObject(r, {})
    const list = unwrapList(raw, [])
    // 字段兼容：created_by->creator/creator_name；approvals->approval_chain；submitted_at/submit_time；补 project_name 映射
    const projMap = {}
    projects.value.forEach(p => { projMap[p.id] = p.name })
    tableData.value = list.map(f => {
      const chain = f.approval_chain || f.approvals || []
      const normalizedChain = chain.map((s, i) => {
        if (typeof s === 'object') {
          let st = 'wait'
          if (s.decision === 'approved' || s.status === 'approved' || s.status === 'pass') st = 'approved'
          else if (s.decision === 'rejected' || s.status === 'rejected' || s.status === 'fail') st = 'rejected'
          else if (s.status === 'current' || s.status === 'pending' || (i === (f.current_step ?? 0) && f.status === 'pending')) st = 'current'
          return {
            role: s.role || s.name || s.approver_role || `步骤${i + 1}`,
            name: s.name || s.user_name || s.approver_name || s.decided_by || '',
            status: st,
            user: s.user || s.user_name || s.decided_by || '',
            time: s.time || s.decided_at || s.created_at || '',
            comment: s.comment || s.decision_comment || '',
          }
        }
        return { role: String(s), name: '', status: 'wait', user: '', time: '' }
      })
      return {
        ...f,
        form_type: f.form_type || f.formType,
        project_name: f.project_name || f.projectName || projMap[f.project_id] || '-',
        creator: f.creator || f.created_by || '',
        creator_name: f.creator_name || f.created_by || '',
        created_at: f.created_at || f.createdAt || '',
        submitted_at: f.submitted_at || f.submit_time || '',
        approval_chain: normalizedChain,
        current_step: f.current_step ?? f.currentStep ?? 0,
        status: f.status,
        form_no: f.form_no || f.formNo || '',
      }
    })
    // 总数兼容
    const tcs = [raw.total, raw.count, raw.page_total, r.total, r.count, r.data?.total, r.data?.count]
    const ft = tcs.find(t => typeof t === 'number')
    pagination.total = typeof ft === 'number' ? ft : tableData.value.length
  } catch {
    // mock
    const mockForms = [
      { id: 1, title: '【施工进度计划】2026年8月施工进度计划', form_type: 'schedule_plan', status: 'pending', project_name: '古贤枢纽左岸边坡开挖', creator: '李工', created_at: '2026-08-03 10:20:00', approval_chain: [{ role: '工程师审核', status: 'pending' }, { role: '项目经理审批', status: '' }, { role: '总监复核', status: '' }], data: { excavation: 85000, backfill: 42000, borrow: 0, waste: 43000 } },
      { id: 2, title: '【变更申请】EL580~EL620段边坡比调整', form_type: 'change_request', status: 'approving', project_name: '古贤枢纽左岸边坡开挖', creator: '张工', created_at: '2026-08-02 16:40:00', approval_chain: [{ role: '工程师审核', status: 'approved', user: '王工', time: '2026-08-02 17:20' }, { role: '项目经理审批', status: 'current' }, { role: '总监复核', status: '' }], data: { location: 'EL580~EL620 段左岸', original_design: '边坡比 1:0.5', proposed_design: '边坡比 1:0.75', reason: '揭露破碎带需放缓边坡', cost_increase_pct: 5.2, delay_days: 3 } },
      { id: 3, title: '【异常报告】S-017传感器速率异常', form_type: 'exception_report', status: 'approved', project_name: '古贤枢纽左岸边坡开挖', creator: '赵工', created_at: '2026-08-01 09:10:00', approval_chain: [{ role: '监测工程师', status: 'approved' }, { role: '技术负责人', status: 'approved' }], approval_history: [{ user: '周工', action: 'approve', time: '2026-08-01 10:00', comment: '已核实，建议加密监测频率' }, { user: '王经理', action: 'approve', time: '2026-08-01 11:30', comment: '同意，按应急预案执行' }], data: { sensor_code: 'S-017', avg_rate: 0.62, threshold: 0.5, analysis: '连续2小时超阈值，判定为黄色预警' } },
      { id: 4, title: '【地质勘察报告】左岸2号钻孔补充勘察', form_type: 'geology_survey', status: 'draft', project_name: '古贤枢纽左岸边坡开挖', creator: '孙工', created_at: '2026-08-03 08:55:00', approval_chain: [], data: { area: '左岸 EL520-EL560', borehole_count: 3, max_depth: 45.5, layer_count: 5 } },
      { id: 5, title: '【监测报告】2026年7月第4周监测周报', form_type: 'monitoring_report', status: 'approved', project_name: '古贤枢纽左岸边坡开挖', creator: '监测组', created_at: '2026-07-28 15:30:00', approval_chain: [{ role: '审核', status: 'approved' }], data: { period_type: 'weekly', point_count: 48, max_displacement: 14.8, max_stress: 2.42, conclusion: '整体稳定，S-017需关注' } },
      { id: 6, title: '【参数计算书】工况15岩土参数反演', form_type: 'param_calculation', status: 'rejected', project_name: '古贤枢纽左岸边坡开挖', creator: '周工', created_at: '2026-07-30 11:00:00', approval_chain: [{ role: '工程师审核', status: 'rejected', user: '王工', time: '2026-07-30 14:20' }], approval_history: [{ user: '王工', action: 'reject', time: '2026-07-30 14:20', comment: '凝聚力取值偏高，建议重新校核试验数据' }], data: { stage: '工况15', method: 'inversion', cohesion: 38.5, friction_angle: 32.6, elastic_modulus: 12.5 } },
      { id: 7, title: '【土石方调配】8月上旬土石方调配方案', form_type: 'earthwork_allocation', status: 'pending', project_name: '古贤枢纽左岸边坡开挖', creator: '李工', created_at: '2026-08-02 14:10:00', approval_chain: [{ role: '工程师审核', status: 'pending' }], data: { total_volume: 12.5, avg_distance: 3.2, equipment: 'truck_30t', efficiency_pct: 85, description: '1号弃渣场为主，临时中转场为辅' } },
    ]
    let filtered = mockForms
    if (activeTab.value !== 'all') filtered = filtered.filter(f => f.status === activeTab.value)
    if (filters.formType) filtered = filtered.filter(f => f.form_type === filters.formType)
    if (filters.keyword) {
      const kw = filters.keyword.toLowerCase()
      filtered = filtered.filter(f => f.title.toLowerCase().includes(kw) || (f.creator || '').toLowerCase().includes(kw))
    }
    tableData.value = filtered
    pagination.total = filtered.length
  } finally {
    tableLoading.value = false
  }
}

// ========== 新建表单 ==========
const createDialogVisible = ref(false)
const createFormRef = ref()
const createForm = reactive({
  form_type: '',
  project_id: '',
  title: '',
  data: {},
})
const createRules = {
  form_type: [{ required: true, message: '请选择表单类型', trigger: 'change' }],
  project_id: [{ required: true, message: '请选择所属项目', trigger: 'change' }],
  title: [{ required: true, message: '请输入表单标题', trigger: 'blur' }],
}

function openCreateDialog() {
  Object.assign(createForm, { form_type: '', project_id: '', title: '', data: {} })
  nextTick(() => { createFormRef.value?.clearValidate() })
  createDialogVisible.value = true
}

function onTypeChange() {
  createForm.data = {}
  // 自动生成标题前缀
  const label = getTypeLabel(createForm.form_type)
  if (!createForm.title && label) {
    const d = new Date()
    const pad = (n) => String(n).padStart(2, '0')
    createForm.title = `【${label}】${d.getFullYear()}年${d.getMonth()+1}月${pad(d.getDate())}日 `
  }
}

async function saveCreateForm(asDraft) {
  await createFormRef.value?.validate()
  const payload = {
    form_type: createForm.form_type,
    project_id: createForm.project_id,
    project_name: projects.value.find(p => p.id === createForm.project_id)?.name,
    title: createForm.title,
    data: createForm.data,
  }
  try {
    const r = await api.createForm(payload)
    if (!asDraft && r?.id) {
      try { await api.submitForm(r.id) } catch {}
    }
    ElMessage.success(asDraft ? '草稿保存成功' : '表单提交成功')
    createDialogVisible.value = false
    await Promise.all([loadForms(), loadStats()])
  } catch {
    ElMessage.success(asDraft ? '草稿保存成功（模拟）' : '表单提交成功（模拟）')
    createDialogVisible.value = false
    await Promise.all([loadForms(), loadStats()])
  }
}
function handleSaveDraft() { saveCreateForm(true) }
function handleCreateSubmit() { saveCreateForm(false) }

// ========== 操作：提交 / 删除 ==========
async function handleSubmit(row) {
  try {
    await api.submitForm(row.id)
    ElMessage.success('提交成功')
  } catch {
    ElMessage.success('提交成功（模拟）')
  }
  await Promise.all([loadForms(), loadStats()])
}

async function handleDelete(row) {
  try {
    await api.deleteForm(row.id)
    ElMessage.success('删除成功')
  } catch {
    ElMessage.success('删除成功（模拟）')
  }
  await Promise.all([loadForms(), loadStats()])
}

// ========== 详情抽屉 ==========
const detailVisible = ref(false)
const currentDetail = ref(null)
const detailLoading = ref(false)
const showApprovalActions = ref(false)
const approvalForm = reactive({ comment: '', action: 'approve' })
const approvalLoading = ref(false)

const detailDrawerTitle = computed(() => {
  if (!currentDetail.value) return '表单详情'
  return showApprovalActions.value ? '审批 - ' + currentDetail.value.title : '详情 - ' + currentDetail.value.title
})

// data 字段配置映射
const dataFieldConfig = {
  schedule_plan: [
    { key: 'excavation', label: '开挖量', unit: ' m³' },
    { key: 'backfill', label: '回填量', unit: ' m³' },
    { key: 'borrow', label: '借方量', unit: ' m³' },
    { key: 'waste', label: '弃方量', unit: ' m³' },
    { key: 'period', label: '施工周期', isDateRange: true, full: true },
    { key: 'waste_sites', label: '弃渣场' },
  ],
  change_request: [
    { key: 'location', label: '变更位置' },
    { key: 'original_design', label: '原设计', full: true },
    { key: 'proposed_design', label: '建议设计', full: true },
    { key: 'reason', label: '变更理由', full: true },
    { key: 'cost_increase_pct', label: '成本增加', unit: ' %' },
    { key: 'delay_days', label: '工期延误', unit: ' 天' },
  ],
  exception_report: [
    { key: 'sensor_code', label: '传感器编号' },
    { key: 'period', label: '监测周期', isDateRange: true },
    { key: 'avg_rate', label: '平均速率', unit: ' mm/h' },
    { key: 'threshold', label: '阈值', unit: ' mm/h' },
    { key: 'analysis', label: '异常分析', full: true },
  ],
  geology_survey: [
    { key: 'area', label: '勘察区域' },
    { key: 'borehole_count', label: '钻孔数量', unit: ' 个' },
    { key: 'max_depth', label: '最大孔深', unit: ' m' },
    { key: 'layer_count', label: '地层数', unit: ' 层' },
    { key: 'conclusion', label: '地质结论', full: true },
  ],
  monitoring_report: [
    { key: 'period_type', label: '报告周期', formatter: (v) => ({ daily: '日报', weekly: '周报', monthly: '月报' }[v] || v) },
    { key: 'point_count', label: '监测点数量', unit: ' 个' },
    { key: 'max_displacement', label: '最大位移', unit: ' mm' },
    { key: 'max_stress', label: '最大应力', unit: ' MPa' },
    { key: 'conclusion', label: '监测结论', full: true },
  ],
  param_calculation: [
    { key: 'stage', label: '计算工况' },
    { key: 'method', label: '计算方法', formatter: (v) => ({ fem: '有限元法 (FEM)', limit_eq: '极限平衡法', inversion: '反演分析法' }[v] || v) },
    { key: 'cohesion', label: '凝聚力 c', unit: ' kPa' },
    { key: 'friction_angle', label: '内摩擦角 φ', unit: ' °' },
    { key: 'elastic_modulus', label: '弹性模量 E', unit: ' GPa' },
    { key: 'result', label: '计算结果说明', full: true },
  ],
  earthwork_allocation: [
    { key: 'period', label: '调配周期', isDateRange: true, full: true },
    { key: 'total_volume', label: '调配方量', unit: ' 万m³' },
    { key: 'avg_distance', label: '平均运距', unit: ' km' },
    { key: 'equipment', label: '运输设备', formatter: (v) => ({ truck_20t: '自卸车 (20t)', truck_30t: '自卸车 (30t)', belt: '皮带机运输' }[v] || v) },
    { key: 'efficiency_pct', label: '调配效率', unit: ' %' },
    { key: 'description', label: '调配方案说明', full: true },
  ],
}

const detailDataFields = computed(() => {
  if (!currentDetail.value) return []
  const data = currentDetail.value.data || {}
  const config = dataFieldConfig[currentDetail.value.form_type]
  if (config) {
    return config.map(c => {
      let val = data[c.key]
      if (c.formatter && val !== undefined && val !== null) val = c.formatter(val)
      return { ...c, value: val }
    })
  }
  // fallback: 渲染所有字段
  return Object.entries(data).map(([k, v]) => ({
    label: k,
    value: typeof v === 'object' ? JSON.stringify(v) : v,
    full: typeof v === 'string' && v.length > 20,
  }))
})

// 审批链 step 状态
function stepStatus(step) {
  if (step.status === 'approved' || step.status === 'pass') return 'success'
  if (step.status === 'rejected' || step.status === 'fail') return 'error'
  if (step.status === 'current' || step.status === 'pending') return 'process'
  return 'wait'
}
function stepIcon(step) {
  const s = stepStatus(step)
  if (s === 'success') return 'Check'
  if (s === 'error') return 'Close'
  return 'User'
}
function stepDescription(step) {
  const parts = []
  if (step.user || step.user_name) parts.push(step.user || step.user_name)
  if (step.time) parts.push(formatDate(step.time))
  if (step.status === 'pending' || step.status === 'current') parts.push('待处理')
  return parts.join(' · ') || (step.status === 'approved' ? '已通过' : '')
}

async function openDetail(row, startApproval = false) {
  detailLoading.value = true
  showApprovalActions.value = false
  approvalForm.comment = ''
  try {
    const r = await api.getForm(row.id)
    const raw = unwrapObject(r, null)
    if (raw && typeof raw === 'object') {
      const projMap = {}
      projects.value.forEach(p => { projMap[p.id] = p.name })
      // 同样规范化 approval_chain
      const chain = raw.approval_chain || raw.approvals || []
      const normalizedChain = chain.map((s, i) => {
        if (typeof s === 'object') {
          let st = 'wait'
          if (s.decision === 'approved' || s.status === 'approved' || s.status === 'pass') st = 'approved'
          else if (s.decision === 'rejected' || s.status === 'rejected' || s.status === 'fail') st = 'rejected'
          else if (s.status === 'current' || s.status === 'pending' || (i === (raw.current_step ?? 0) && raw.status === 'pending')) st = 'current'
          return {
            role: s.role || s.name || s.approver_role || `步骤${i + 1}`,
            name: s.name || s.user_name || s.approver_name || s.decided_by || '',
            status: st,
            user: s.user || s.user_name || s.decided_by || '',
            time: s.time || s.decided_at || s.created_at || '',
            comment: s.comment || s.decision_comment || '',
          }
        }
        return { role: String(s), name: '', status: 'wait', user: '', time: '' }
      })
      // 规范化 approval_history：从 approvals 中生成或直接使用
      let history = raw.approval_history
      if (!Array.isArray(history) || !history.length) {
        history = normalizedChain
          .filter(s => s.status === 'approved' || s.status === 'rejected')
          .map(s => ({
            user: s.user || s.name,
            user_name: s.name || s.user,
            action: s.status === 'approved' ? 'approve' : 'reject',
            time: s.time,
            comment: s.comment,
          }))
      }
      currentDetail.value = {
        ...raw,
        form_type: raw.form_type || raw.formType,
        project_name: raw.project_name || raw.projectName || projMap[raw.project_id] || row.project_name || '-',
        creator: raw.creator || raw.created_by || '',
        creator_name: raw.creator_name || raw.created_by || '',
        created_at: raw.created_at || raw.createdAt || '',
        submitted_at: raw.submitted_at || raw.submit_time || '',
        approval_chain: normalizedChain,
        approval_history: history,
        current_step: raw.current_step ?? raw.currentStep ?? 0,
        status: raw.status,
        form_no: raw.form_no || raw.formNo || '',
      }
    } else {
      currentDetail.value = { ...row }
    }
  } catch {
    currentDetail.value = { ...row }
  } finally {
    detailLoading.value = false
  }
  detailVisible.value = true
  if (startApproval) {
    showApprovalActions.value = true
  }
}

function beforeCloseDetail(done) {
  if (showApprovalActions.value && approvalForm.comment) {
    ElMessageBox.confirm('当前有未提交的审批意见，确定关闭吗？', '提示', { type: 'warning' })
      .then(() => { showApprovalActions.value = false; done() })
      .catch(() => {})
  } else {
    done()
  }
}

// ========== 审批 ==========
async function handleApprove(action) {
  approvalForm.action = action
  if (action === 'reject' && !approvalForm.comment.trim()) {
    ElMessage.warning('驳回必须填写理由')
    return
  }
  approvalLoading.value = true
  try {
    await api.approveForm(currentDetail.value.id, {
      action,
      comment: approvalForm.comment,
    })
    ElMessage.success(action === 'approve' ? '审批通过' : '已驳回')
    showApprovalActions.value = false
    detailVisible.value = false
    await Promise.all([loadForms(), loadStats()])
  } catch {
    ElMessage.success(action === 'approve' ? '审批通过（模拟）' : '已驳回（模拟）')
    showApprovalActions.value = false
    detailVisible.value = false
    await Promise.all([loadForms(), loadStats()])
  } finally {
    approvalLoading.value = false
  }
}

// ========== 初始化 ==========
onMounted(async () => {
  await Promise.all([
    loadFormTypes(),
    loadProjects(),
    loadStats(),
    loadForms(),
  ])
})

watch(activeTab, (v) => {
  const q = { ...route.query }
  q.tab = v === 'all' ? undefined : v
  // 仅更新 query 不触发重载
  if (route.query.tab !== (q.tab || undefined)) {
    // router.replace({ query: q })
  }
})
</script>

<style scoped>
.form-approval-page {
  padding: 20px;
  min-height: 100%;
}

/* ===== 页面头部 ===== */
.page-header { margin-bottom: 16px; }
.header-left .page-title {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  display: flex; align-items: center; gap: 10px;
}
.header-left .page-subtitle {
  margin: 0; font-size: 13px; color: #64748b;
}

/* ===== Tabs ===== */
.tab-bar {
  display: flex;
  gap: 6px;
  background: #fff;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 1px 3px rgba(15,23,42,0.04);
  margin-bottom: 14px;
  overflow-x: auto;
}
.tab-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 14px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  border: 1px solid transparent;
}
.tab-item:hover { background: #f8fafc; color: #334155; }
.tab-item.active {
  background: #eff6ff;
  color: #2563eb;
  font-weight: 600;
  border-color: #bfdbfe;
}
.tab-label { line-height: 1; }

/* ===== 筛选区 ===== */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  padding: 14px 18px;
  border-radius: 12px;
  border: 1px solid #f1f5f9;
  margin-bottom: 14px;
  gap: 12px;
  flex-wrap: wrap;
}
.filter-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.filter-right { display: flex; align-items: center; gap: 10px; }
.filter-select { width: 170px; }
.filter-input { width: 260px; }

/* ===== 统计条 ===== */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 14px;
}
.stats-mini-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px 18px;
  border: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  gap: 14px;
  position: relative;
  overflow: hidden;
  transition: transform 0.2s;
}
.stats-mini-card:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(15,23,42,0.06); }
.stats-mini-card::before {
  content: '';
  position: absolute; top: 0; left: 0;
  width: 4px; height: 100%;
}
.stats-icon {
  width: 44px; height: 44px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.stats-value {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.1;
}
.stats-label {
  font-size: 12.5px;
  color: #64748b;
  margin-top: 3px;
}
.sm-blue::before { background: #3b82f6; }
.sm-blue .stats-icon { background: #dbeafe; color: #3b82f6; }
.sm-orange::before { background: #f59e0b; }
.sm-orange .stats-icon { background: #fef3c7; color: #f59e0b; }
.sm-green::before { background: #10b981; }
.sm-green .stats-icon { background: #d1fae5; color: #10b981; }
.sm-red::before { background: #ef4444; }
.sm-red .stats-icon { background: #fee2e2; color: #ef4444; }

/* ===== 表格卡片 ===== */
.table-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #f1f5f9;
  padding: 16px 0 0;
  overflow: hidden;
}
.col-title {
  display: flex; align-items: center; gap: 8px;
}
.title-text {
  color: #1d4ed8;
  cursor: pointer;
  font-weight: 500;
}
.title-text:hover { text-decoration: underline; }
.col-project {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: #475569;
}
.col-user {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px;
}
.user-avatar {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
}
.col-time {
  font-size: 13px;
  color: #64748b;
  font-family: 'Segoe UI', monospace;
}
.col-step {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.col-step :deep(.el-steps) { flex-grow: 0; width: 100px; }
.step-label {
  font-size: 11.5px;
  color: #64748b;
}
.col-step-simple {
  font-size: 13px;
  color: #64748b;
}

.pagination-wrap {
  padding: 16px 20px 20px;
  display: flex;
  justify-content: flex-end;
}

/* ===== 抽屉 ===== */
.divider-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 6px;
}
.approval-chain {
  background: #f8fafc;
  padding: 16px 18px;
  border-radius: 10px;
  border: 1px solid #f1f5f9;
  margin-bottom: 4px;
}
.chain-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 14px;
  display: flex; align-items: center; gap: 6px;
}
.desc-info { margin-bottom: 8px; }
.desc-data { margin-bottom: 8px; }
.empty-val { color: #94a3b8; }

.approval-history {
  padding: 8px 4px 0;
}
.history-item { padding: 2px 0; }
.history-title {
  font-size: 13.5px;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}
.history-comment {
  font-size: 12.5px;
  color: #64748b;
  background: #f8fafc;
  padding: 6px 10px;
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
}

.approval-actions {
  position: sticky;
  bottom: 0;
  background: #fff;
  margin: 0 -20px -20px;
  padding: 0 20px 16px;
}
.actions-btns {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* ===== 动态表单 ===== */
.dynamic-form-section {
  background: #fafbfc;
  padding: 4px 12px 0;
  border-radius: 10px;
  border: 1px solid #f1f5f9;
}

/* ===== 响应式 ===== */
@media (max-width: 1200px) {
  .stats-bar { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .filter-select { width: 140px; }
  .filter-input { width: 200px; }
}
</style>
