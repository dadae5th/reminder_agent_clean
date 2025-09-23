// Supabase Edge Function으로 완료 처리
// 이 함수는 Supabase에서 직접 실행되므로 별도 서버가 필요 없습니다

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // CORS 처리
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // URL에서 토큰 추출
    const url = new URL(req.url)
    const token = url.searchParams.get('token')
    
    if (!token) {
      return new Response('토큰이 필요합니다', { 
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'text/html; charset=utf-8' }
      })
    }

    // Supabase 클라이언트 초기화
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseServiceKey)

    // 토큰으로 업무 찾기
    const { data: tasks, error: selectError } = await supabase
      .from('tasks')
      .select('*')
      .eq('hmac_token', token)
      .eq('status', 'pending')
      .limit(1)

    if (selectError) {
      console.error('업무 조회 오류:', selectError)
      return new Response('데이터베이스 오류', { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'text/html; charset=utf-8' }
      })
    }

    if (!tasks || tasks.length === 0) {
      return new Response(`
        <html>
          <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h2>⚠️ 처리할 수 없습니다</h2>
            <p>이미 완료되었거나 토큰이 유효하지 않습니다.</p>
            <p><a href="${Deno.env.get('DASHBOARD_URL') || '#'}" style="color: #007bff;">📊 대시보드 보기</a></p>
          </body>
        </html>
      `, {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'text/html; charset=utf-8' }
      })
    }

    const task = tasks[0]

    // 업무 완료 처리
    const now = new Date().toISOString()
    const { error: updateError } = await supabase
      .from('tasks')
      .update({ 
        status: 'done', 
        last_completed_at: now,
        updated_at: now
      })
      .eq('id', task.id)

    if (updateError) {
      console.error('업무 완료 처리 오류:', updateError)
      return new Response('업무 완료 처리 중 오류가 발생했습니다', { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'text/html; charset=utf-8' }
      })
    }

    console.log(`✅ 업무 완료: ${task.title} (ID: ${task.id})`)

    // 성공 페이지 반환
    return new Response(`
      <html>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
          <h2>✅ 완료되었습니다!</h2>
          <p><strong>${task.title}</strong> 업무가 성공적으로 완료되었습니다.</p>
          <p>완료 시간: ${new Date(now).toLocaleString('ko-KR')}</p>
          <p><a href="${Deno.env.get('DASHBOARD_URL') || '#'}" style="color: #007bff;">📊 대시보드 보기</a></p>
        </body>
      </html>
    `, {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'text/html; charset=utf-8' }
    })

  } catch (error) {
    console.error('오류:', error)
    return new Response(`
      <html>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
          <h2>❌ 오류 발생</h2>
          <p>업무 완료 처리 중 오류가 발생했습니다: ${error.message}</p>
          <p><a href="${Deno.env.get('DASHBOARD_URL') || '#'}" style="color: #007bff;">📊 대시보드 보기</a></p>
        </body>
      </html>
    `, {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'text/html; charset=utf-8' }
    })
  }
})
